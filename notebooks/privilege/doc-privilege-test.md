> ⚠️ **MEASURED RECONCILIATION (2026-07-02, Polaris 1.3.0).** This document is the *original hypothesis* set. Live runs refuted parts of it — see **`doc-privilege-results.md`** for the source-of-truth measurements. Key corrections: (1) reading a single view needs **`VIEW_READ_PROPERTIES`**, not `VIEW_LIST` (§2); (2) `CATALOG_MANAGE_METADATA` is **not read-only** — it authorizes create/drop/commit (§1, §3 Use Case C); (3) all privilege names below were accepted at grant time (no `GRANT_INVALID`); (4) **added 2026-07-06** — "Table DROP (with or without a file purge)" is actually two different ops with two different privilege requirements: `TABLE_DROP` alone only covers the plain drop; a *purging* drop (`?purgeRequested=true`) needs `CATALOG_MANAGE_CONTENT` and is NOT bypassed by root/service_admin (§2, `purge/doc-purge-troubleshooting.md`, `purge/table_purge_privilege_test.ipynb`). Inline `MEASURED:` notes flag each spot.

### Analysis of the `CREATE_NAMESPACE` Authorization Failure

The `403 Forbidden` error encountered by your Service Principal (`vptest-c1-inst-prin`) represents a clean perimeter rejection by the Apache Polaris access control engine.

During the execution of Case **C1**, the runner initialized an isolated instance principal with a baseline privilege profile consisting strictly of `["TABLE_LIST", "VIEW_LIST", "VIEW_CREATE"]`. However, the test framework subsequently issued a `POST /api/catalog/v1/{catalog}/namespaces` command using that principal's authentication headers to scaffold the environment. Because creating a namespace requires either the explicit granular grant of `NAMESPACE_CREATE` or the master parent grant of `CATALOG_MANAGE_CONTENT`, Polaris blocked the operation before it could ever touch the view layer.

To master Polaris security architecture and eliminate these boundary errors, you must understand the relational mapping between API verbs, securable objects, and minimal privilege requirements.

---

### 1. The Apache Polaris Privilege Hierarchy Tree

Polaris governs security using two dimensions: **Securable Hierarchies** (the targets of a grant) and **Privilege Cascades** (the strength of a grant).

#### Securable Inheritance

Grants follow a cascading model down the resource organization tree. When a privilege is granted at a higher level, it automatically blankets all child entities nested underneath it:

* **Catalog Scopes:** Grants applied here cascade down to every namespace, table, and view contained within that catalog.
* **Namespace Scopes:** Grants applied here apply to all tables and views nested inside this specific namespace, protecting adjacent namespaces from cross-tenant access.
* **Entity Scopes:** Grants applied directly to a singular Table or View isolate permissions to that specific metadata asset.

#### Privilege Power Cascades

At any given securable level, coarse-grained administrative privileges encompass fine-grained operational privileges. This eliminates the need to assign dozens of individual permissions to high-level system components.

```
[CATALOG_MANAGE_CONTENT]
   ├── NAMESPACE_CREATE / NAMESPACE_DROP
   ├── TABLE_CREATE / TABLE_DROP
   └── VIEW_CREATE / VIEW_DROP

[CATALOG_MANAGE_METADATA]
   ├── TABLE_READ_DATA / TABLE_WRITE_DATA (Schema Commits)
   └── VIEW_LIST / TABLE_LIST

```

> **MEASURED:** on this build the split above does not hold — **both** coarse masters authorize the *full* action set (namespace/table/view create, list, drop, read, commit, get). `CATALOG_MANAGE_METADATA` is not a metadata-read-only master; it grants mutation too. See `doc-privilege-results.md` §3.

---

### 2. Comprehensive Minimal Privilege Action Matrix

This matrix maps out the absolute minimal authorizing grant required for every major REST Catalog API verb and entity mutation under the Apache Iceberg REST specification.

| Target Securable | REST Verb & Endpoint Pattern | Data Operations Covered | Absolute Minimal Privilege | Coarse Master Override |
| --- | --- | --- | --- | --- |
| **Namespace** | `POST /v1/{cat}/namespaces` | Creating a metadata directory layer. | `NAMESPACE_CREATE` | `CATALOG_MANAGE_CONTENT` |
| **Namespace** | `GET /v1/{cat}/namespaces` | Listing available namespaces. | `NAMESPACE_LIST` | `CATALOG_MANAGE_METADATA` |
| **Namespace** | `DELETE /v1/{cat}/namespaces/{ns}` | Dropping an empty namespace structural node. | `NAMESPACE_DROP` | `CATALOG_MANAGE_CONTENT` |
| **Table** | `POST /v1/{cat}/namespaces/{ns}/tables` | Instantiating a brand new Iceberg table asset. | `TABLE_CREATE` | `CATALOG_MANAGE_CONTENT` |
| **Table** | `GET /v1/{cat}/namespaces/{ns}/tables` | Listing table names within a namespace. | `TABLE_LIST` | `CATALOG_MANAGE_METADATA` |
| **Table** | `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` | Committing a new snapshot append or schema update. | `TABLE_WRITE_DATA` | `CATALOG_MANAGE_METADATA` |
| **Table** | `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` | Fetching the live metadata-location string to read data. | `TABLE_READ_DATA` | `CATALOG_MANAGE_METADATA` |
| **Table** | `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` | Dropping the table record, **plain (no purge)**. | `TABLE_DROP` | `CATALOG_MANAGE_CONTENT` |
| **Table** | `DELETE .../tables/{tbl}?purgeRequested=true` | Dropping the table record **with a file purge**. | ⚠️ *MEASURED (2026-07-06):* NOT `TABLE_DROP` alone — that returns `403 "is not authorized for op DROP_TABLE_WITH_PURGE"`, even for root/service_admin. See `doc-privilege-results.md`. | `CATALOG_MANAGE_CONTENT` (confirmed sufficient) |
| **View** | `POST /v1/{cat}/namespaces/{ns}/views` | Instantiating a fresh Iceberg SQL View definition. | `VIEW_CREATE` | `CATALOG_MANAGE_CONTENT` |
| **View** | `GET /v1/{cat}/namespaces/{ns}/views/{vw}` | Reading back the SQL query text and view schema mapping. | `VIEW_READ_PROPERTIES` ⟵ *MEASURED (not `VIEW_LIST`, which returns 403 here)* | `CATALOG_MANAGE_METADATA` |
| **View** | `DELETE /v1/{cat}/namespaces/{ns}/views/{vw}` | Removing the view registration from the catalog. | `VIEW_DROP` | `CATALOG_MANAGE_CONTENT` |

---

### 3. Real-World Use Case Catalog Roles

In production enterprise deployments, you should avoid using the global root identity for application connections. Instead, map your infrastructure requirements into four classic, highly secure Catalog Roles:

#### Use Case A: The Automated Data Ingestion Pipeline (Data Engineer)

* **Business Profile:** An automated Apache Spark, Flink, or DBT worker responsible for landing raw source logs into storage, creating daily partition partitions, and running structural optimizations.
* **Assigned Privilege Footprint:** `["NAMESPACE_CREATE", "TABLE_CREATE", "TABLE_WRITE_DATA", "TABLE_READ_DATA", "VIEW_CREATE"]`
* **Boundary Enforcement:** This identity can build and maintain datasets but is explicitly blocked from dropping tables or purging storage buckets, protecting production assets from accidental code defects.

#### Use Case B: The Business Intelligence Analyst (Data Consumer)

* **Business Profile:** A data analyst querying dashboards via Trino, StarRocks, or Athena. They require full visibility to read records and construct aggregate business views, but must never modify raw backend data.
* **Assigned Privilege Footprint:** `["TABLE_LIST", "TABLE_READ_DATA", "VIEW_LIST", "VIEW_CREATE"]`
* **Boundary Enforcement:** Fully read-only on physical tables. They can create local, personal analytical views to save specialized queries but cannot perform schema evolution or run table drops.
* **MEASURED (6/7):** the footprint is right *except* it cannot read a single view — `VIEW_LIST` authorizes listing views but not `GET /views/{view}` (→ 403). Add **`VIEW_READ_PROPERTIES`** to let analysts open a view's definition.

#### Use Case C: The Data Governance & Compliance Officer (Auditor)

* **Business Profile:** A security officer auditing table history, schema modifications, access vectors, and metadata file trails across the entire organization.
* **Assigned Privilege Footprint:** `["CATALOG_MANAGE_METADATA"]`
* **Boundary Enforcement:** Can review the structure, lifecycle properties, and metadata paths of every single table and view across the catalog. However, they are blocked from seeing the actual raw rows inside the data files (`TABLE_READ_DATA` is absent), keeping sensitive records hidden during metadata evaluations.
* **MEASURED (4/10 — footprint is wrong):** on this build `CATALOG_MANAGE_METADATA` is **not read-only** — it authorizes CREATE/DROP/COMMIT on namespaces, tables, and views, so this "auditor" is actually a full read-write admin. For a genuinely read-only auditor, grant the granular read set instead: `NAMESPACE_LIST, TABLE_LIST, TABLE_READ_DATA` (or `TABLE_READ_PROPERTIES`), `VIEW_LIST, VIEW_READ_PROPERTIES`. (Raw-row hiding is enforced at credential-vending, not the REST catalog API.)

#### Use Case D: The Catalog Tenant Administrator (Tenant Manager)

* **Business Profile:** A dedicated administrator overseeing a single business unit's catalog domain.
* **Assigned Privilege Footprint:** `["CATALOG_MANAGE_CONTENT"]`
* **Boundary Enforcement:** Holds sovereign command over all structure creation, metadata alterations, and table/view deconstructions inside that singular catalog. They cannot access sibling catalogs, read management layer configuration maps, or manipulate cluster service principals.

---

### 4. Privilege Testing Strategy & Framework Design

To construct an automated, programmatic testing framework that verifies these security boundaries without causing configuration sprawl or state corruption, implement a **Three-Stage Lifecycle Routine**:

#### Stage 1: Sandbox Isolation Setup

* **Action:** For every privilege scenario under evaluation, the master administrative identity spins up a completely isolated catalog using a unique tracking token name (e.g., `test-privilege-table-drop`).
* **Scaffolding Isolation:** The master token sets up the parent namespace nodes and populates the specific test tables or views. This guarantees the underlying entity is valid before the authorization check occurs.

#### Stage 2: The Challenge Phase

* **Action:** The master identity boots a brand new, single-use Service Principal assigned **exclusively** to a dedicated Principal-Role. This role receives exactly *one* scoping privilege from your matrix (e.g., only `VIEW_DROP`).
* **Execution:** The test runner requests an OAuth token explicitly scoped to that single principal-role. It challenges the targeted REST catalog API endpoint and logs the resulting HTTP status code:
* **HTTP 403 (Authorized Mismatch):** Proves that the privilege under test successfully acts as a locked gate against unauthorized traffic.
* **HTTP 200/204 (Authorized Match):** Programmatically establishes that the minimal required privilege criteria has been successfully identified.



#### Stage 3: Bottom-Up Sterilization

* **Action:** To prevent metadata leakage or connection-pool starvation from ghost records, the test suite routes final execution through a mandatory `finally` block.
* **Erasure Workflow:** The master token bypasses the restricted test roles, explicitly deletes the target table or view, drops the empty parent namespaces, deletes the custom catalog role mappings, de-registers the temporary service principal, and reclaims physical file footprints directly from object storage. This ensures each subsequent evaluation start begins on a clean, predictable slate.