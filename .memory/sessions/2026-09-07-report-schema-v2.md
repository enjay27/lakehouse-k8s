# 2026-09-07 — report schema v2: two corrections and six new fields

**What was done:** the nine changes proposed in
[`logging/HANDOFF-report-schema-v2-2026-09-07.md`](../../logging/HANDOFF-report-schema-v2-2026-09-07.md)
were implemented in `logging/fb-values.yaml`, minus `top_error_path`. `SCHEMA_VERSION` is
now **2**. Nothing has been deployed — this is written and not running, like every schema
change in this repo until Kade upgrades the shipper.

## The decisions, and who made them

| § | question | decision |
|---|---|---|
| 8.1 | bump the schema, or add parallel names | **bump to v2**, with both renames. The only consumer is the coverage harness, and it changes in the same pass |
| 8.2 | `top_error_path` | **out**. `resources_other_distinct` answers the security question; a free-text path on a summary that has none is a separate argument |
| 8.3 | `level: INFO` or keep `REPORT` | **keep `REPORT`**. It is the stream selector every existing query and the harness's `vlogs.py` use. The cost — the severity column is meaningless for this stream — is now stated in the Lua rather than discovered |
| 8.4 | one upgrade with the fast-run revert, or two | **two, schema first** (Kade). v2 ships on top of `WINDOW_SECONDS 30` / `Interval_Sec 5` so a fast coverage run can exercise the new fields; the revert to 1800/30 is its own upgrade afterwards |
| 8.5 | `windows_skipped` at all | **in**, with the caveat carried in the code comment: on this cluster it is routinely non-zero because the OrbStack VM suspends with the laptop |

## The two corrections, restated as what changed in the numbers

- **`distinct_resources` / `distinct_principals` counted rows emitted, not resources
  touched.** `new_window` increments `n_resources` for every zero-carry key, so the quiet
  window in the test suite reported **3 resources with 0 access lines**. They now count rows
  with `requests > 0`; the carried rows moved to **`carried_rows`**, so zero-carry stays
  visible without inflating a cardinality number. The suite's quiet-window case now asserts
  `distinct_resources 0, carried_rows 5` where it asserted `3`.
- **`counted_get` counted HEAD as well** — `READ_METHODS` is GET *and* HEAD, and the summary
  printed the number as `%d GET`. Renamed **`counted_read`**, printed as `read`.

## Added

`errors_4xx` / `errors_5xx` / `auth_denied` on the summary and on every resource and
principal row — `errors` stays the total, so nothing that reads it breaks. A 404 is traffic
and a 500 is an incident, and v1 put both in one integer. **`status == nil` (unparsed) is an
error but is charged to neither split**, so `errors_4xx + errors_5xx <= errors` is a real
invariant rather than an identity.

`bytes_total` (summed over resources, not principals — the margins are equal, summing both
would double-count), `resources_other_distinct` (folded *keys*, capped at
`REPORT_MAX_RESOURCES`, where `resources_other` counts folded *requests*),
`windows_skipped`, and `seq=` / `@hostname` / byte counts in the `_msg` strings.

## Verified — and what "verified" means here

`logging/scripts/test-polaris-filters.py`: **60/60**, run against a real Lua 5.4 in the
Cowork container (the bridge VM has no interpreter; the values file was staged up, edited,
tested, and committed back). Eight new report cases: HEAD → `counted_read`; a 500 on a known
resource → `errors_5xx`; two invented table names hit three times → `resources_other 3,
resources_other_distinct 2`; 401 and 403 → `auth_denied` and `errors_4xx` both; a tick
jumping two indices → `windows_skipped 2`; carried rows excluded from `distinct_resources`.
The expected values were computed by hand from the record list, not read off the
implementation.

**New suite 4 closes §4's trap mechanically.** It reads `type_int_key` out of
`config.filters` and the emitted field names out of the Lua — same file both times — and
fails if a numeric field is missing from the list *or* if the list names a field the report
no longer emits. Confirmed to fail by deleting `auth_denied` from the directive, then
restored. This is the check that would have caught `counted_get` being left in the list
after the rename.

**NOT verified:** `helm lint` and `helm upgrade --dry-run` — no cluster reach from a Cowork
session. Nor has any of this run in Fluent Bit: the deployed Lua is LuaJIT/5.1, the suite ran
on 5.4, and nothing here uses a 5.2+ construct, but that is an argument, not a measurement.

## What has to move with it, and is not in this commit

The harness in `polaris-practice/polaris-learning/` is not mounted in a Cowork session.
`SUMMARY_FIELDS` / `RESOURCE_FIELDS` / `PRINCIPAL_FIELDS` are frozen sets and will fail
loudly on the new names — which is the point. `diff_reports` must **exclude
`windows_skipped`** like `partial_window`: it is a property of the emitting process's clock
and no oracle can predict it. The characterization test goes red on `SCHEMA_VERSION 2`;
read the diff, then update it and `doc-log-coverage-results.md` together.
