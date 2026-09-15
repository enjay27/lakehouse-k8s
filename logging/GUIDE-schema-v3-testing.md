# Testing report schema v3 — for the `polaris-learning` notebook

Seven gates, in order. Each says what **passing** looks like and, more importantly, **what would
make it fail** — this pipeline's recurring defect is gates that cannot fail, so a gate whose failure
mode you cannot state is not yet a gate.

Schema reference: [`SCHEMA-report.md`](SCHEMA-report.md). Query mechanics and the OpenSearch traps:
[`GUIDE-opensearch-notebook.md`](GUIDE-opensearch-notebook.md).

```python
import requests, os, urllib3, json; urllib3.disable_warnings()
OS   = "https://192.168.194.1:9200"
AUTH = ("admin", os.environ["OS_PASSWORD"])
def q(idx, body):
    r = requests.post(f"{OS}/{idx}/_search", json=body, auth=AUTH, verify=False, timeout=30)
    r.raise_for_status(); return r.json()
V3 = {"term": {"schema_version": 3}}          # ALWAYS. v2 and v3 coexist in the index.
```

## Read this before running any gate below — `.keyword`, always

**Every `term` filter on a STRING field must name the `.keyword` subfield.** These indices are
dynamic-mapped, so `resource`, `resource_kind`, `api_kind`, `report_type`, `http_method`,
`window_start` are `text` with a `.keyword` beside them. A `term` query is **not** analysed but the
*field* is, so it is matched against the analyser's output:

| written | analysed to | matches |
|---|---|---|
| `{"term": {"resource": "__errors__"}}` | `errors` | **never** |
| `{"term": {"resource_kind": "catalog-role"}}` | `catalog`, `role` | **never** |
| `{"term": {"http_method": "POST"}}` | `post` | **never** — uppercase cannot match |
| `{"term": {"resource_kind": "other"}}` | `other` | works, by luck of being one lowercase token |

Every version of this guide before 2026-09-10 got this wrong in Gates 2, 4 and 5, and the failure is
the one this pipeline keeps producing: **a gate that matches nothing reports zero and PASSES.** Run
1789026666 caught it on Gate 5. Numeric fields (`schema_version`, `requests`) and `exists` are
unaffected.

## And pin the window — never `sort desc` + `size N`

Row-level gates below took the most recent N documents and read the answer off them. **Zero-carry
rows make that wrong by construction**: a resource that goes quiet is re-emitted with every counter
at 0 for one more window, so the newest documents for a key are usually its zeros, and the window
that actually carried the traffic is further down. `auth_denied: 0` read that way says nothing at
all.

Drive the traffic, note the wall clock, and filter `{"term": {"window_start.keyword":
"2026-09-10T07:52:00Z"}}` — the window you drove into. **Match by `window_start`, never by
position.**

---

## Gate 0 — is v3 actually running

```python
q("polaris-report-*", {"size":1, "query":{"bool":{"filter":[V3]}},
                       "sort":[{"@timestamp":"desc"}]})
```

**PASS** — a document comes back, and its `window_start` is recent.
**FAILS IF** — no hits. Then the ConfigMap changed but the pod never rolled, or the roll never
happened. `step5-probe-apply-verify.sh --apply` checks both halves; do not diagnose anything else
until this passes. Reading `schema_version` out of `fluent-bit/values.yaml` proves nothing.

## Gate 1 — the margin invariants

```python
r = q("polaris-report-*", {"size":0, "query":{"bool":{"filter":[V3,
        {"range":{"@timestamp":{"gte":"now-10m"}}}]}},
      "aggs":{"by_win":{"terms":{"field":"window_start.keyword","size":40},
        "aggs":{"by_type":{"terms":{"field":"report_type.keyword"},
                  "aggs":{"req":{"sum":{"field":"requests"}}}},
                "seen":{"sum":{"field":"access_seen"}},
                "parse":{"sum":{"field":"parse_errors"}}}}})
```
For each window: `sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors`.

**PASS** — exact on every window with traffic.
**FAILS IF** — a resource row is dropped without its requests being accounted for. This is the gate
that caught the `excluded_requests` design before it shipped.
⚠ `sum` returns `0.0` for an absent field, so pair every `sum` with a `value_count` — a window with
no v3 rows will otherwise report a tidy `0 == 0`.

## Gate 2 — THE FEATURE. Everything else tests plumbing.

`last_write_bytes` on a table row must equal the `response_size` of the **actual commit** that
produced it. Drive one commit, then:

```python
# 1. the report's claim
q("polaris-report-*", {"size":5, "query":{"bool":{"filter":[V3,
     {"term":{"report_type.keyword":"resource"}}, {"term":{"resource_kind.keyword":"table"}},
     {"term":{"window_start.keyword":W}},          # W = the window you drove the commit into
     {"exists":{"field":"last_write_bytes"}}]}},
   "_source":["window_start","resource","last_write_bytes","writes"]})

# 2. the record it should have come from
q("polaris-logs-*", {"size":5, "query":{"bool":{"filter":[
     {"term":{"http_method.keyword":"POST"}}, {"wildcard":{"api_path.keyword":"*/tables/*"}},
     {"range":{"@timestamp":{"gte":"<window_start>","lt":"<window_end>"}}}]}},
   "sort":[{"@timestamp":"desc"}], "_source":["@timestamp","api_path","http_status","response_size"]})
```

**PASS** — the report's `last_write_bytes` equals the `response_size` of the **last 2xx POST** in
that window on that table.
**FAILS IF** — it matches the *first* commit (last-wins broken), or a 500's size (2xx filter
broken), or 0 (the `> 0` guard broken), or the field is absent when a commit did happen.

Then the negative case, which is the half people skip: a window whose only write was a
`DELETE` (204, empty) must have **no** `last_write_bytes` at all — absent, not `0`.

⚠ **A window of carried rows is not evidence.** Run 1789026666 reported this gate VOID — "2 table
rows in the window and none carries `last_write_bytes`" — which is the expected reading of a window
whose table rows are zero-carries. Add `{"range":{"requests":{"gt":0}}}` so the gate can only look
at rows that saw traffic, and drive the commit into a window you then name. **Until this gate passes
once, v3 is unproven**: `last_write_bytes` is the feature and every other gate here tests plumbing
that already worked in v2.

## Gate 3 — classification

```python
q("polaris-report-*", {"size":0, "query":{"bool":{"filter":[V3,
     {"term":{"report_type":"resource"}}]}},
   "aggs":{"api":{"terms":{"field":"api_kind.keyword"},
     "aggs":{"kind":{"terms":{"field":"resource_kind.keyword","size":20}}}}}})
```

**PASS** — `api_kind` is `management` / `catalog` / `mixed`, and **`resource_kind` never reads
`management`** (it is an API surface, and it now lives in `api_kind`).
**FAILS IF** — `resource_kind: management` appears at all, or `api_kind` is missing on a resource
row, or a catalog-role has `api_kind: catalog` (it is served by the management API).

## Gate 4 — roles, and the privilege count

```python
q("polaris-report-*", {"size":20, "query":{"bool":{"filter":[V3,
     {"term":{"resource_kind.keyword":"catalog-role"}},
     {"term":{"window_start.keyword":W}}]}},      # W = the window you drove the grants into
   "_source":["window_start","resource","requests","reads","writes","auth_denied"]})
```

**`writes` on a `catalog-role` row is the number of privileges granted in that window.**

**PASS** — a role you granted N privileges to reports `writes == N`, and no separate row exists
for the `…/grants` path.
**FAILS IF** — a `…/catalog-roles/{cr}/grants` row appears on its own (the fold broke), or the
assignment path `/principal-roles/{pr}/catalog-roles/{cat}` keys to the **catalog** role instead of
the principal role (rule ordering broke).

⚠ **`writes` is per WINDOW, and not every grant-shaped call lands on this row.** Run 1789026666
read `writes=1` against `granted=3` and called it a FAIL. Two ways to get that without a filter
fault: the three grants straddled 30s boundaries, or one of them was
`PUT /principal-roles/{pr}/catalog-roles/{cat}`, which keys to the **principal** role — the rule
ordering this same gate declares correct. Count N *within the named window*, on the *same* role.

Then the denial case: a **403** on a catalog role with no successful request in the same window must
still produce that role's row, with `auth_denied: 1`, and increment `role_keys_forced` on the
summary. If it lands in `__errors__` instead, the `ROLE_KINDS` exemption is not working.

**Read `role_keys_forced` FIRST — it is the direct evidence, and `auth_denied` on a row is
downstream of it:**

```python
q("polaris-report-*", {"size":1, "query":{"bool":{"filter":[V3,
     {"term":{"report_type.keyword":"summary"}}, {"term":{"window_start.keyword":W}}]}},
   "_source":["window_start","role_keys_forced","auth_denied","errors_4xx"]})
```

`role_keys_forced >= 1` means the exemption fired and the role row exists; `0` with a 403 driven in
that window means it really did fall to `__errors__`. Reading `auth_denied: 0` off a row list
sorted by time answers neither question — see the window-pinning note at the top.

## Gate 5 — the two synthetic buckets mean different things

```python
q("polaris-report-*", {"size":0, "query":{"bool":{"filter":[V3]}},
   "aggs":{"synthetic":{"filters":{"filters":{
       "errors":{"term":{"resource.keyword":"__errors__"}},
       "other":{"term":{"resource.keyword":"__other__"}}}},
     "aggs":{"req":{"sum":{"field":"requests"}},"err":{"sum":{"field":"errors"}}}}}})
```

**PASS** — `__errors__` has `requests == errors` (it holds nothing but errors), and `__other__` is
**absent or zero** unless a window really carried 500+ distinct resources.
**FAILS IF** — `__other__` has traffic while `resources_other == 0`, which would mean the split
regressed and the two populations are sharing a bucket again.

**Attribution is lost, the record is not.** Every one of those errored requests is stored in full in
`polaris-logs-*` by rule 3 — find them in Discover by `http_status >= 400` over the window.

## Gate 6 — what still needs a classification rule

```python
q("polaris-report-*", {"size":0, "query":{"bool":{"filter":[V3,
     {"term":{"resource_kind.keyword":"other"}}, {"range":{"requests":{"gt":0}}}]}},
   "aggs":{"by_api":{"terms":{"field":"api_kind.keyword"},
     "aggs":{"paths":{"terms":{"field":"resource.keyword","size":50}}}}}})
```

**PASS** — only `__errors__` / `__other__` come back.
**Anything else is a real path with no rule**, showing its exact URL and API surface. That is the
maintenance signal for a newly added endpoint; add a `RESOURCE_PATTERNS` entry and re-run.

**This gate has only ever been driven once against the whole API.** Run 1789026666 drove all 63
operations from the vendored OpenAPI documents and found exactly one such path —
`/api/catalog/v1/{cat}/transactions/commit` — now classified as `transaction`
(`fluent-bit/values.yaml`, 2026-09-10). A gate that has never seen traffic on an endpoint cannot
report that endpoint missing, so **the coverage of the driver is part of this gate**, not a
detail of the harness.

## Gate 7 — the Lua unit test, before any of the above

```bash
cp fluent-bit/polaris_access_log.lua /tmp/polaris.lua   # its own file since 2026-09-15 (was luaScripts in values.yaml)
lua5.4 logging/scripts/test-schema-v3.lua
```

**58 assertions** against the **deployed script text** (46 before 2026-09-10; the twelve new ones
cover the `transaction` kind and the absent-not-`""` `min/max_record_time`). Needs a Lua
interpreter — the Fluent Bit image is distroless and the Cowork VM has none, so run it wherever
`lua5.4` exists. **58/58 on 2026-09-10**, against the values file as edited that day.

Run this **first** when anything looks wrong: it separates "the filter is wrong" from "my query is
wrong" in one step, and it has already caught an invalid Lua escape that would have failed the whole
chunk at load.

---

## Traps carried over

- **Filter `schema_version: 3` on every query.** v1, v2 and v3 rows share the index; an unfiltered
  aggregation silently mixes them.
- **`_time` is the window's END.** `window_start 05:59:00` carries `_time 05:59:30`.
- **`report_seq` is per pod** — pair it with `hostname` or two pod generations invent a gap.
- **Absence is not zero.** `sum` returns `0.0` for a field that does not exist; pair with
  `value_count`.
- **`min_record_time` was mapped as `text`** in `polaris-report-2026.09.09` and again in
  `2026-09-10` — the Lua wrote `""` on idle windows and OpenSearch typed the field from the first
  one. **Fixed on both sides, 2026-09-10**: the Lua now omits the key when nil, and
  `logging/opensearch/polaris-report-template.json` types both fields as `date`
  (`bash logging/scripts/step9-report-index-template.sh`). Neither is retroactive — indices up to
  and including `2026-09-10` stay `text` for their life, so do no date maths on those.
- **A gate that matches nothing PASSES.** Pair every `sum` with a `value_count`, and every `term`
  on a string field with `.keyword`. Both are the same failure wearing different clothes.
