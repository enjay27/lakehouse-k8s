# HANDOFF — schema v2 is live and correct; the harness disagrees with it in three ways, all its own

**Written 2026-09-07 for `polaris-practice/polaris-learning/`, from `local-k8s`.** Run
`1788755035` drove 146 calls against a shipper running report schema **v2**
(`fb-values.yaml` sha256 `d58b9203a8304030`; the notebook's own gate confirms the running
ConfigMap carries that script). The run reports **34 fixture mismatches — FAILING** and a
violated invariant. **None of them is a filter fault.** Every one is the harness measuring v2
with v1 assumptions, and two of the three are the kind that returns a wrong number rather than
an error.

## First: the pipeline is right, and here is the arithmetic

From the report stream itself, window `2026-09-07T04:24:00Z` (`seq=6`), 44 resource rows and
4 principal rows read out of VMUI and summed independently of both the filter and the oracle:

| | resources | principals | summary |
|---|---|---|---|
| `requests` | **158** | **158** | `access_seen` **158** |
| `errors` | 41 | 41 | `errors_kept` 41 |
| `errors_4xx` | 41 | 41 | 41 |
| `auth_denied` | 12 | 12 | 12 |
| `response_bytes` | 1,186,348 | 1,186,348 | `bytes_total` 1,186,348 |

`access_kept 68 + access_counted 90 = 158`; `counted_read 73 + counted_post 17 = 90`.

**The v2 fields carry their own margins.** In v1 the only self-check was the request margin;
`errors_4xx`, `auth_denied` and `bytes_total` now each reconcile across two independently
built row sets, so a filter that attributed an error to the wrong principal would show up.
This is a stronger check than the one the schema shipped with, and it passed on first contact.

Cardinality reconciles too: **38 active resources + 4 active principals + 6 carried = 48 rows**
emitted, and the next window (`seq=7`) carries exactly **42** — the 38 + 4 that were active —
then decays to 0 in `seq=8`. That is the v1 defect fixed, visible end to end: `seq=7` reports
`0 resources, 0 principals, 42 carried` where v1 would have claimed 42 resources touched in a
window with no traffic at all.

## Bug 1 — the window merge does not sum fields it does not know about

**This is the one to fix first, because it silently reports a wrong number.**

The run merges two windows (`04:23:30`, 24 rows; `04:24:00`, 49 rows). For a field the merge
knows, values are summed. For a v2 field they are not — the first window's value survives:

| row / field | oracle | stored (merged) | live `04:24:00` row | live `04:23:30` |
|---|---|---|---|---|
| `principal nb_…_principal` `errors` | 28 | **26** | 25 | 1 → summed ✓ |
| `principal nb_…_principal` `errors_4xx` | 28 | **1** | 25 | 1 → **not summed** |
| `resource …/tables/probe_tbl` `auth_denied` | 10 | **0** | 10 | 0 → **not summed** |

Same signature on `probe_tbl errors_4xx`, `…/namespaces errors_4xx` and
`…/probe_ns/tables errors_4xx` — every one is a v2 field, and every one reads as a single
window rather than the merge.

**Fix:** derive the summable set from the row's own numeric keys instead of a hardcoded list.
A literal field list has now produced this failure mode twice — once here and once as
`type_int_key` — and both times the symptom was a plausible number, not an exception. If the
list must stay literal, it needs a test that fails when a report row carries a numeric field
the list does not name.

## Bug 2 — `distinct_resources=38 but 44 resource rows were emitted` is the new correct behaviour

The invariant checker flags this. It was right for v1 and is wrong for v2: the six extra rows
are zero-carry rows, and not counting them is the entire point of the change.

**Replace it with the stronger form**, which the live window satisfies exactly:

```
distinct_resources + distinct_principals + carried_rows == (rows emitted) - 1   # 38 + 4 + 6 == 48
```

and add, per row set: `errors_4xx + errors_5xx <= errors` (a `nil` status is an error charged
to neither split, so this is an inequality on purpose) and `auth_denied <= errors_4xx`.

## Bug 3 — the oracle does not predict the v2 fields, and one of them it never can

`SUMMARY_FIELDS` / `RESOURCE_FIELDS` / `PRINCIPAL_FIELDS` report the new names as *unexpected*
and `counted_get` as *missing*. That is the frozen sets doing their job. Update them:

- add `errors_4xx`, `errors_5xx`, `auth_denied`, `bytes_total`, `carried_rows`,
  `resources_other_distinct`, `windows_skipped`, `counted_read`; drop `counted_get`;
- the oracle must **compute** `errors_4xx` / `errors_5xx` / `auth_denied` from each call's
  status (401 and 403 count as denied *and* as 4xx), and `counted_read` from GET **and HEAD** —
  the rename exists because v1 called HEADs GETs;
- **`windows_skipped` must be excluded from the diff**, like `partial_window`. It is a property
  of the emitting process's clock; no oracle can predict it, and on this cluster it is
  routinely non-zero because the OrbStack VM suspends with the laptop.

The characterization test goes red on `SCHEMA_VERSION 2`. That is by design — read the diff,
then update it and `doc-log-coverage-results.md` together.

## Two smaller things this run showed

- **`resources_other_distinct` is not asserted anywhere.** The run asserts `resources_other > 0`
  (27 requests folded) but nothing about how many distinct keys those were. That field exists to
  separate one broken client from a scanner; give it the assertion.
- **The notebook's own prose still says "Schema v1, three record types on one envelope."**
  It is v2. The line is in the flush-report section of the results template.
