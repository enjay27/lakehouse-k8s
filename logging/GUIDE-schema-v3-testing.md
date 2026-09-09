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
     {"term":{"report_type":"resource"}}, {"term":{"resource_kind":"table"}},
     {"exists":{"field":"last_write_bytes"}}]}}, "sort":[{"@timestamp":"desc"}],
   "_source":["window_start","resource","last_write_bytes","writes"]})

# 2. the record it should have come from
q("polaris-logs-*", {"size":5, "query":{"bool":{"filter":[
     {"term":{"http_method":"POST"}}, {"wildcard":{"api_path":"*/tables/*"}},
     {"range":{"@timestamp":{"gte":"<window_start>","lt":"<window_end>"}}}]}},
   "sort":[{"@timestamp":"desc"}], "_source":["@timestamp","api_path","http_status","response_size"]})
```

**PASS** — the report's `last_write_bytes` equals the `response_size` of the **last 2xx POST** in
that window on that table.
**FAILS IF** — it matches the *first* commit (last-wins broken), or a 500's size (2xx filter
broken), or 0 (the `> 0` guard broken), or the field is absent when a commit did happen.

Then the negative case, which is the half people skip: a window whose only write was a
`DELETE` (204, empty) must have **no** `last_write_bytes` at all — absent, not `0`.

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
     {"term":{"resource_kind":"catalog-role"}}]}}, "sort":[{"@timestamp":"desc"}],
   "_source":["window_start","resource","requests","reads","writes","auth_denied"]})
```

**`writes` on a `catalog-role` row is the number of privileges granted in that window.**

**PASS** — a role you granted N privileges to reports `writes == N`, and no separate row exists
for the `…/grants` path.
**FAILS IF** — a `…/catalog-roles/{cr}/grants` row appears on its own (the fold broke), or the
assignment path `/principal-roles/{pr}/catalog-roles/{cat}` keys to the **catalog** role instead of
the principal role (rule ordering broke).

Then the denial case: a **403** on a catalog role with no successful request in the same window must
still produce that role's row, with `auth_denied: 1`, and increment `role_keys_forced` on the
summary. If it lands in `__errors__` instead, the `ROLE_KINDS` exemption is not working.

## Gate 5 — the two synthetic buckets mean different things

```python
q("polaris-report-*", {"size":0, "query":{"bool":{"filter":[V3]}},
   "aggs":{"synthetic":{"filters":{"filters":{
       "errors":{"term":{"resource":"__errors__"}},
       "other":{"term":{"resource":"__other__"}}}},
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
     {"term":{"resource_kind":"other"}}, {"range":{"requests":{"gt":0}}}]}},
   "aggs":{"by_api":{"terms":{"field":"api_kind.keyword"},
     "aggs":{"paths":{"terms":{"field":"resource.keyword","size":50}}}}}})
```

**PASS** — only `__errors__` / `__other__` come back.
**Anything else is a real path with no rule**, showing its exact URL and API surface. That is the
maintenance signal for a newly added endpoint; add a `RESOURCE_PATTERNS` entry and re-run.

## Gate 7 — the Lua unit test, before any of the above

```bash
python3 -c "import yaml;print(yaml.safe_load(open('fluent-bit/values.yaml'))['luaScripts']['polaris_access_log.lua'])" > /tmp/polaris.lua
lua5.4 logging/scripts/test-schema-v3.lua
```

46 assertions against the **deployed script text**. Needs a Lua interpreter — the Fluent Bit image
is distroless and the Cowork VM has none, so run it wherever `lua5.4` exists.

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
- **`min_record_time` is mapped as `text` in `polaris-report-2026.09.09`** — the Lua writes `""` on
  idle windows and OpenSearch typed the field from the first one. No date maths on it in that index.
  A new index will map correctly only once the Lua omits the key instead. Not yet fixed.
