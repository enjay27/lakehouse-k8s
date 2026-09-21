# Polaris Privilege — Measured Results

**Date:** 2026-07-02 (table-DROP-WITH-PURGE addendum: 2026-07-06)
**Build:** Apache Polaris 1.3.0 · env `local` (OrbStack single-node)
**Source runs:** `polaris_privilege_matrix_test.ipynb`, `polaris_privilege_hierarchy_test.ipynb`, `polaris_use_case_roles_test.ipynb` (all `Restart & Run All`, zero harness-bug flags, zero leaked entities). Table-purge addendum sourced from `purge/table_purge_privilege_test.ipynb` (live run 2026-07-06) and `purge/table_view_purge_privilege_test.ipynb`.

This document records the **empirically measured** authorization behavior of this build. Where it disagrees with the earlier claims in `doc-privilege-test.md` (the privilege tree §1, minimal matrix §2, role profiles §3), the measurement wins — those claims were hypotheses; see [§6 Refutations](#6-refutations-of-the-source-claims).

---

## 1. Minimum granular privilege per action (matrix)

Each action was challenged with one privilege at a time by a single-privilege worker. `all authorizing` lists every single privilege that returned 2xx.

| Target | Action (REST verb) | Minimal privilege (measured) | Also sufficient |
|---|---|---|---|
| Namespace | CREATE (POST) | `NAMESPACE_CREATE` | `CATALOG_MANAGE_CONTENT` |
| Namespace | LIST (GET) | `NAMESPACE_LIST` | `CATALOG_MANAGE_METADATA`, `CATALOG_MANAGE_CONTENT` |
| Namespace | DROP (DELETE) | `NAMESPACE_DROP` | `CATALOG_MANAGE_CONTENT` |
| Table | CREATE (POST) | `TABLE_CREATE` | `CATALOG_MANAGE_CONTENT` |
| Table | LIST (GET) | `TABLE_LIST` | `CATALOG_MANAGE_METADATA`, `CATALOG_MANAGE_CONTENT` |
| Table | READ (GET metadata) | `TABLE_READ_DATA` *or* `TABLE_READ_PROPERTIES` | `CATALOG_MANAGE_METADATA`, `CATALOG_MANAGE_CONTENT` |
| Table | COMMIT (POST update) | `TABLE_WRITE_DATA` *or* `TABLE_WRITE_PROPERTIES` | `CATALOG_MANAGE_METADATA`, `CATALOG_MANAGE_CONTENT` |
| Table | DROP, plain (DELETE, no `purgeRequested`) | `TABLE_DROP` | `CATALOG_MANAGE_CONTENT` |
| Table | DROP **WITH PURGE** (DELETE `?purgeRequested=true`) | ⚠️ **NOT** `TABLE_DROP` alone — see below | `CATALOG_MANAGE_CONTENT` |
| View | CREATE (POST) | `VIEW_CREATE` | `CATALOG_MANAGE_CONTENT` |
| View | GET (GET one view) | **`VIEW_READ_PROPERTIES`** | `CATALOG_MANAGE_METADATA`, `CATALOG_MANAGE_CONTENT` |
| View | DROP (DELETE) | `VIEW_DROP` | `CATALOG_MANAGE_METADATA`, `CATALOG_MANAGE_CONTENT` |

**Headline finding — reading a single view:** `VIEW_LIST` does **not** authorize `GET /views/{view}` — it returns `403 BLOCKED_PRIV`. The minimum for reading a view definition is **`VIEW_READ_PROPERTIES`**. (`VIEW_LIST` only authorizes listing views in a namespace.)

**Headline finding — table DROP is not one action, it's two (measured live 2026-07-06, `purge/table_purge_privilege_test.ipynb`):** a *plain* `DELETE` (no `purgeRequested`) and a *purging* `DELETE ?purgeRequested=true` are gated by **different ops** — `DROP_TABLE` vs `DROP_TABLE_WITH_PURGE`. The row above (`TABLE_DROP` minimal) only holds for the plain drop. For the purging drop:

```
TABLE_DROP alone                    -> 403 "is not authorized for op DROP_TABLE_WITH_PURGE"  (measured, non-root AND root)
CATALOG_MANAGE_CONTENT              -> 204 (sufficient, measured)
TABLE_DROP + TABLE_WRITE_DATA        -> not independently re-tested this run; this is the minimal
                                        granular pair per purge/doc-purge-troubleshooting.md's
                                        earlier "Layer 2" finding (2026-06-29) -- flagged here as
                                        an OPEN item, not yet re-confirmed against this measurement
```

**Also new:** root/`service_admin` does **NOT** bypass `DROP_TABLE_WITH_PURGE` — it must hold `CATALOG_MANAGE_CONTENT` on the catalog like anyone else. This is a genuine difference from `View DROP` (root/service_admin bypasses that one entirely, confirmed in `view_purge_behavior_test.ipynb`'s C9). It also means this matrix's own "Non-root rule" (root only bootstraps, per `doc-privilege-matrix-plan.md` §6) never actually tested root against this specific op — nothing here previously contradicted it, the purge op just wasn't in scope until now.

**Also new — gate precedence:** when BOTH the config gate (`drop-with-purge.enabled=false`) and the privilege gate (missing `CATALOG_MANAGE_CONTENT`) are violated at once, Polaris returns the **PRIVILEGE** 403 (`"is not authorized"`), not the CONFIG one (`"Unable to purge entity"`). Authorization is checked before the config flag. See `purge/table_purge_privilege_test.ipynb` cases P1–P3.

**Necessity (all 11/11 confirmed):** granting an unrelated privilege (`VIEW_LIST`, or `TABLE_LIST` for the view case) blocked every action with `403 BLOCKED_PRIV` — so each minimal privilege above is genuinely *necessary*, not merely sufficient.

---

## 2. Privilege vocabulary (this build)

All 16 privilege names exercised were **accepted at grant time** — **zero `GRANT_INVALID`**:

```
CATALOG_MANAGE_CONTENT   CATALOG_MANAGE_METADATA
NAMESPACE_CREATE  NAMESPACE_LIST  NAMESPACE_DROP
TABLE_CREATE  TABLE_LIST  TABLE_READ_DATA  TABLE_READ_PROPERTIES
TABLE_WRITE_DATA  TABLE_WRITE_PROPERTIES  TABLE_DROP
VIEW_CREATE  VIEW_LIST  VIEW_READ_PROPERTIES  VIEW_DROP
```

This overturns the earlier assumption (matrix plan §3) that `NAMESPACE_*`, `TABLE_READ_DATA`, `TABLE_WRITE_DATA`, etc. might be rejected — they are all valid on this build.

---

## 3. Coarse-master cascade (hierarchy)

Granting **only** a coarse master and probing every action:

| Action | `CATALOG_MANAGE_CONTENT` | `CATALOG_MANAGE_METADATA` |
|---|---|---|
| Namespace.CREATE | ✅ AUTHORIZED | ✅ AUTHORIZED |
| Namespace.LIST | ✅ AUTHORIZED | ✅ AUTHORIZED |
| Namespace.DROP | ✅ AUTHORIZED | ✅ AUTHORIZED |
| Table.CREATE | ✅ AUTHORIZED | ✅ AUTHORIZED |
| Table.LIST | ✅ AUTHORIZED | ✅ AUTHORIZED |
| Table.READ | ✅ AUTHORIZED | ✅ AUTHORIZED |
| Table.COMMIT | ✅ AUTHORIZED | ✅ AUTHORIZED |
| Table.DROP | ✅ AUTHORIZED | ✅ AUTHORIZED |
| View.CREATE | ✅ AUTHORIZED | ✅ AUTHORIZED |
| View.GET | ✅ AUTHORIZED | ✅ AUTHORIZED |
| View.DROP | ✅ AUTHORIZED | ✅ AUTHORIZED |

**Both coarse masters authorize every action tested.** `CATALOG_MANAGE_METADATA` is **not** a read-only / metadata-only privilege on this build — it authorizes CREATE, DROP, and COMMIT on namespaces, tables, and views, just like `CATALOG_MANAGE_CONTENT`.

**Securable inheritance — CONFIRMED:** a grant made at the catalog-role (catalog) level reaches entities nested below it (namespace → table/view). A `CATALOG_MANAGE_CONTENT` holder could READ/DROP/GET a table and view nested under the namespace.

---

## 4. Real-world role verdicts

| Role | Footprint | Verdict | Notes |
|---|---|---|---|
| **A · Data Engineer** | `NAMESPACE_CREATE, TABLE_CREATE, TABLE_WRITE_DATA, TABLE_READ_DATA, VIEW_CREATE` | ✅ **PASS 8/8** | Creates/writes/reads; blocked from every drop. Footprint is correct as written. |
| **B · BI Analyst** | `TABLE_LIST, TABLE_READ_DATA, VIEW_LIST, VIEW_CREATE` | ⚠️ **6/7** | Only miss: `View.GET → 403`. `VIEW_LIST` does not cover reading a single view; needs `VIEW_READ_PROPERTIES`. |
| **C · Auditor** | `CATALOG_MANAGE_METADATA` | ⚠️ **4/10** | Read side works, but the whole *deny* side (create/drop) is `AUTHORIZED`: CMM is not read-only, so this footprint gives a full read-write admin, not an auditor. |
| **D · Tenant Admin** | `CATALOG_MANAGE_CONTENT` | ✅ **PASS 7/7** | Full control within its catalog; **cross-catalog drop blocked (403)** — sovereignty is per-catalog, confirmed. |

---

## 5. What holds up from the source docs

- Every granular `*_CREATE / *_LIST / *_DROP` privilege is the correct minimum for its action (matrix §2 rows other than View.GET).
- `CATALOG_MANAGE_CONTENT` is a full master over structure/content — confirmed.
- Securable inheritance (catalog → namespace → entity) — confirmed.
- Per-catalog isolation (a grant on catalog X does not reach catalog Y) — confirmed.
- The three-stage scaffold→worker→sterilize lifecycle and the six-way outcome taxonomy behaved cleanly (no `BLOCKED_OPA` / `BLOCKED_CONFIG` / `GRANT_INVALID` / `LAG_500`).

## 6. Refutations of the source claims

| Source claim (`doc-privilege-test.md`) | Measured reality |
|---|---|
| §1/§3 — `CATALOG_MANAGE_METADATA` exposes metadata but not mutation ("read-only auditor") | CMM authorizes CREATE/DROP/COMMIT on ns/table/view — **not read-only**. |
| §2 — reading a single view needs `VIEW_LIST` | Needs **`VIEW_READ_PROPERTIES`**; `VIEW_LIST` → `403`. |
| §2/matrix-plan §3 — several privilege names may be rejected at grant | **All 16 accepted**; zero `GRANT_INVALID`. |
| §1 — the cascade tree splits CMC (structure) vs CMM (metadata read) | On this build both masters authorize the full action set tested. |
| §2 (`doc-privilege-test.md` row "Table DROP ... with or without a file purge") — `TABLE_DROP` covers both a plain drop and a purging drop | Refuted for the purging case: `TABLE_DROP` alone → `403` on `DROP_TABLE_WITH_PURGE` (measured 2026-07-06). Only holds for the plain drop. |

## 7. Recommended corrections to the role footprints

- **BI Analyst:** add **`VIEW_READ_PROPERTIES`** (keep `VIEW_LIST` for listing) so analysts can open a view's definition, not just enumerate views.
- **Auditor (read-only intent):** do **not** use `CATALOG_MANAGE_METADATA` — it grants full mutation here. For a genuinely read-only auditor, grant the granular read set: `NAMESPACE_LIST, TABLE_LIST, TABLE_READ_DATA` (or `TABLE_READ_PROPERTIES`), `VIEW_LIST, VIEW_READ_PROPERTIES`. (Note: even these do not restrict raw-row access, which is gated at credential-vending / object storage, outside the REST catalog API this harness drives.)
- **Data Engineer / Tenant Admin:** no change — both verified correct.
