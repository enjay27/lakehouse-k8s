# PLAN — report schema v3: latest response body size per resource

**Status: PROPOSED. Nothing changed.** Three decisions are marked **DECIDE** and the plan should
not be applied until they are answered — each one changes what the number means.

**Requirement (manager, via Kade):** the *latest* response body size for each resource, especially
**table commit** and **get table**.

## 1. What the schema already has, and why it is not the answer

Resource rows carry `response_bytes` — a **sum over the window**. A sum cannot answer "how big was
the last commit response"; a table with 40 reads and one commit reports one number containing both.

What makes this cheap: **commit and get are not different resources.** Both hit
`^.-/namespaces/[^/]+/tables/[^/]+`, so `resource_kind = "table"` with the same resource key. They
differ by **method** — the Lua already splits `READ_METHODS = {GET, HEAD}` from
`WRITE_METHODS = {POST, PUT, DELETE, PATCH}`, and `response_size` is already parsed per record
(`fluent-bit/values.yaml:161`). So the data is in hand at filter time; only the accumulator changes.

Note this holds even though **policy v3 stores no individual record for a successful GET** — it is
*counted only*. The filter still sees it, so the size is capturable. This is the one place the
report can carry information that exists nowhere else, which is exactly why `access_counted` was
worth having.

## 2. Proposed fields on the `resource` row

```
last_read_bytes      last successful-or-not GET/HEAD response size in this window
last_read_status     the HTTP status that produced it
last_write_bytes     last POST/PUT/DELETE/PATCH response size in this window
last_write_status    the HTTP status that produced it
last_write_method    POST | PUT | DELETE | PATCH  -- see DECIDE 2
```

`last_write_method` is what separates a **commit** (`POST` on a table) from a **drop**
(`DELETE`, typically an empty 204). Without it, `last_write_bytes` silently blends them and the
manager's number is sometimes a commit and sometimes a zero-length delete, with nothing to say
which. **Same field for principals** if wanted; the row shapes are parallel. *Not proposed* —
the request is about resources.

## 3. DECIDED (Kade, 2026-09-09) — and the rule set collapses the schema

**Two fields only. No status, no method.**

```
last_read_bytes     last GET/HEAD response size in this window
last_write_bytes    last POST/PUT/DELETE/PATCH response size in this window
```

Sampling rule, applied per record, last-wins:

1. **overwrite on every qualifying request** — no averaging, no first-wins;
2. **2xx only** — an error document's length is not "the response size";
3. **size > 0 only** — and if nothing in the window qualified, **the field is absent**, never `0`.

### Why dropping `last_write_method` is right, not a compromise

I proposed it to stop a commit blending with a drop. **Rule 3 removes that problem at the source**,
and the resource patterns show why:

| on a `resource_kind = "table"` row | verb | body | in `last_write_bytes`? |
|---|---|---|---|
| commit — `POST .../tables/{table}` | POST | table metadata | **yes** |
| drop — `DELETE .../tables/{table}` | DELETE | 204, empty | no — size 0 |
| create — `POST .../tables` | POST | metadata | no — that is `kind = "collection"`, a different row |

So on a table row **`last_write_bytes` *is* the last successful commit**, with no method field
needed. The same rule does the same favour on the read side: `HEAD` (tableExists) carries no body
by definition, so `last_read_bytes` on a table row is the last successful **loadTable**, with HEADs
excluded automatically.

`RESOURCE_PATTERNS` (`fluent-bit/values.yaml:246`) is what makes this hold — create hits the
`tables$` collection pattern, commit hits `tables/[^/]+`. This is read off the repo, not off the
Iceberg spec.

### Why dropping the status fields costs nothing

The worry was distinguishing "no traffic" from "all traffic errored" from "all bodies empty". **The
row already answers that**: it carries `requests`, `reads`, `writes`, `errors`, `errors_4xx`,
`errors_5xx`. So `writes > 0` with `last_write_bytes` absent means every write was an error or
empty-bodied — recoverable from fields that already exist. No new field earns its place.

### Zero-carry rows follow from rule 3, and are hereby decided

A carried row has no requests, so nothing qualifies, so **both fields are absent**. That is
option (a) from the original draft: *absence is not zero*, and "latest ever" stays a query —
sort by `@timestamp` desc, take the first row where the field exists.

### One residue, not a blocker

**"Last" means last-processed.** For a single Polaris pod that equals last-logged, because the tail
reads one file in order. If `#8`'s HPA ever became live, three replicas would write three files and
the DaemonSet would interleave them arbitrarily — "last" would then be ill-defined across replicas.
The HPA currently reports `cpu: <unknown>` and cannot scale, so this is dormant. Worth knowing
before anyone re-enables it.

## 6. Consequences that are not the Lua

- **`SCHEMA_VERSION` 2 -> 3.** There will then be **three** versions in `polaris-report-*`. Trap #4
  in the guide already says an unfiltered aggregation over mixed versions silently reduces sums —
  with v3 that gets worse, not better. **Every consumer query must filter `schema_version`**, and
  `GUIDE-opensearch-notebook.md` §4 needs the new fields before the notebook is written.
- **`type_int_key` must list every new integer field** (`last_read_bytes`, `last_read_status`,
  `last_write_bytes`, `last_write_status`) on *both* Lua filter blocks. Omit one and Fluent Bit
  encodes it as a double — the `404.0` bug that made numeric filters silently match nothing.
  `last_write_method` is a string and must **not** be listed.
- **Sequencing.** The Lua lives in `polaris_access_log.lua`, shared by both releases. Editing it
  breaks byte-identity with `fb-polaris-shipper`. That constraint existed to keep the stdout-vs-file
  comparison valid — **that comparison is banked (265 == 265)**, so it no longer binds. Cleanest
  order is still: uninstall the shipper, then this. If this lands first, the two releases diverge
  and any further shipper comparison is void.
- **Do this BEFORE the new notebook**, which is why the request arrived now. Writing the notebook
  against v2 and then changing the schema means writing it twice.
- **Volume.** Four to five more fields on every resource row, and resource rows are the bulk of the
  report stream. At the temporary 30s window that is ~60x the steady-state row rate — another
  reason the 1800/30 revert should not drift.

## 7. Gates

1. **`schema_version` reads 3 from a stored document**, not from the file.
2. **The margin equality still holds**: `sum(resource.requests) == sum(principal.requests) ==
   access_seen - parse_errors`. Adding fields should not disturb it; run it because "should not" is
   how this week went.
3. **The number is right, checked by hand.** Drive one table commit, find the access-log record for
   it, and confirm `last_write_bytes` on that resource's row **equals the `response_size` on that
   record**. This is the only gate that tests the feature rather than its plumbing, and it can fail.
4. **Carry behaviour matches DECIDE 1.** Drive traffic to a table, then leave it idle one window,
   and confirm the carried row does what was chosen — absent, or carried with its window stamp.
5. `report_seq` continuity unbroken across the change (`hi - lo + 1 == n`, one hostname).

## 8. Not verifiable from a Cowork session
No `helm lint`, no `--dry-run`, no cluster reach. Apply with
`logging/scripts/step5-probe-apply-verify.sh --apply`, which renders, confirms the ConfigMap, rolls,
and confirms the running process.
