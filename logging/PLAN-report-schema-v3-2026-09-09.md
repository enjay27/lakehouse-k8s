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

## 3. DECIDE 1 — what "latest" means across a window with no traffic

Zero-carry emits a row for a resource that fell to zero requests, so the fall is visible. What
should `last_*` read on such a row?

- **(a) Absent — recommended.** No sample this window, no field. The pipeline's own rule is
  *absence is not zero* (`POLARIS-LOGGING-GUIDE` §7.4 #5), and a stale byte count sitting in a
  "latest" field is precisely the plausible-wrong-number this pipeline keeps producing. "Latest
  ever" is then a **query**, not a schema feature: sort by `@timestamp` desc and take the first row
  where the field exists — three lines in the notebook, and always correct.
- **(b) Carry the previous value**, plus a `last_read_window` / `last_write_window` so staleness is
  visible. Two more fields, and every consumer must remember to check them.
- **(c) Carry silently.** Cheapest, and the option that will eventually put a number from an hour
  ago on a dashboard labelled "latest". **Do not choose this.**

## 4. DECIDE 2 — should errors count as "the latest response"?

A 500's body is an error document; its size is not "the response size" in the sense the manager
means. Options: capture regardless and expose `last_*_status` so the consumer filters (recommended
— the filtering is one clause and the raw fact is preserved), or only sample 2xx and lose the
ability to see that the last commit failed.

## 5. DECIDE 3 — is a `0` meaningful?

`record["response_size"] = tonumber(size) or 0` turns a logged `-` (no body) into `0`, so a zero is
ambiguous between *empty body* and *unparsed*. Recommendation: **only update `last_*` when the
record parsed** (`parse_failed` false), leaving genuine empty bodies as a true 0. Cheap, and it
keeps the ambiguity out of the field.

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
