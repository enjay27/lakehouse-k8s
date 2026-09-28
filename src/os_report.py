"""Query the OpenSearch half of the Polaris log pipeline.

WHY THIS MODULE EXISTS
----------------------
Until 2026-09-18 two Fluent Bits ran the same Lua: the DaemonSet
`benchmarks-fluent-bit` (CRI stdout -> OpenSearch) and the Deployment
`fb-polaris-shipper` (PVC `polaris.log` -> VictoriaLogs), with its own LogsQL
client `vlogs.py`. The shipper, VictoriaLogs and `vlogs.py` are gone; the
DaemonSet is the pipeline. `polaris_test_utils.os_client()` speaks to OpenSearch
but is pinned to `k8s-logs-*`, the stock DaemonSet index, which is NOT
`polaris-report-*` / `polaris-logs-*` -- so this module exists to query those.

WHAT IS ENFORCED HERE RATHER THAN LEFT TO CALL SITES
----------------------------------------------------
Each of these has already cost this project a wrong answer once. A rule that
lives in prose gets forgotten at one call site out of twenty, and the one that
forgets is the one that reports a tidy zero:

1.  **`schema_version` is filtered on every report query.** v1, v2 and v3 rows
    share the index -- measured 2026-09-10: 1465 v2 rows and 63 v3 rows in the
    same pattern. An unfiltered aggregation mixes them silently. `_filters()`
    adds the term; there is no path to a report query without it short of
    calling `raw_search`, which is named to be conspicuous in a diff.

2.  **Every `sum` is paired with a `value_count`.** OpenSearch returns
    `{"value": 0.0}` for a sum over a field that does not exist in any matching
    document, which is indistinguishable from a real zero. `Metric.absent` is
    the difference, and `Metric.value` is **None** when nothing carried the
    field. The guide flags this; here it is impossible to skip.

3.  **String terms use `.keyword`.** `{"term": {"resource": "__errors__"}}` --
    written exactly that way in the guide's Gate 5 -- runs against the analysed
    `text` field, where the standard analyser has already turned `__errors__`
    into the token `errors`. The term never matches, the aggregation reports
    zero, and Gate 5 passes forever without ever having looked. `kw()` appends
    the suffix and `assert_keyword_ready()` proves the subfield exists before a
    run trusts any of it.

4.  **Counts are scoped to a window range and stamped.** The report index is
    written continuously -- one row per window, 2/min at WINDOW_SECONDS=30 --
    so two counts taken across two queries disagree by elapsed time alone. That
    nearly produced a finding about 55 lost rows on 2026-09-10; they were the
    clock. Reconciling figures come back from ONE query (`margins()`), and
    every result carries `taken_at`.

The pure builders (`q_*`) and parsers (`parse_*`) hold all the logic and take no
client, so the rules above are testable without a cluster, a drive, or a window
boundary to wait for.
"""

import datetime as _dt
import time as _time

import requests

DEFAULT_REPORT_INDEX = "polaris-report-*"
DEFAULT_LOGS_INDEX = "polaris-logs-*"
DEFAULT_TIMEOUT = 30

#: The schema this module asserts against. Read the DEPLOYED value out of the
#: running ConfigMap and compare -- never assume this constant is current. It is
#: the constant that was one version stale on 2026-09-07 and rendered every
#: correct row as "eight unexpected fields".
SCHEMA_VERSION = 3

REPORT_TYPES = ("summary", "resource", "principal")

#: The two synthetic resource keys. They mean DIFFERENT things in v3 and the
#: split is the point of Gate 5: `__errors__` holds errored requests whose
#: resource was not already known (attribution lost, record still stored in full
#: by rule 3), `__other__` holds genuine overflow past REPORT_MAX_RESOURCES.
#: Before v3 both shared the `__other__` name and the measured split was 38
#: errors to 0 overflow -- the row was named after the case that never occurred.
ERRORS_KEY = "__errors__"
OTHER_KEY = "__other__"
SYNTHETIC_KEYS = (ERRORS_KEY, OTHER_KEY)

#: Fields OpenSearch dynamic-maps as `text` + `.keyword`. A term filter or a
#: terms aggregation on any of these MUST use the subfield.
STRING_FIELDS = frozenset(
    {
        "report_type",
        "window_start",
        "window_end",
        "hostname",
        "app",
        "level",
        "resource",
        "resource_kind",
        "api_kind",
        "user_principal_name",
        # CORRELATION RESTS ON THIS ONE. A request id is
        # `nb-<run>-<seq>-<label>` and the standard analyser splits it on
        # every hyphen, so a term or prefix query against the analysed
        # field matches NOTHING: every call reports unrecovered and the
        # per-call half of the matrix reads as a total pipeline failure
        # rather than as a query bug. Found 2026-09-10 while wiring the v2
        # notebook -- the same defect this module was written to catch in
        # the guide's Gate 5, sitting in this module.
        "mdc.requestId",
        "partial_window",
        "min_record_time",
        "max_record_time",
        "_msg",
        "api_path",
        "http_method",
    }
)

#: Fields the deployed filter hands to `type_int_key`. If any of these comes
#: back mapped as text, every `sum` in gates 1-5 is wrong and the run is void.
NUMERIC_FIELDS = frozenset(
    {
        "schema_version",
        "report_seq",
        "window_seconds",
        "access_seen",
        "access_kept",
        "access_counted",
        "counted_read",
        "counted_post",
        "errors_kept",
        "parse_errors",
        "errors_4xx",
        "errors_5xx",
        "auth_denied",
        "bytes_total",
        "distinct_resources",
        "distinct_principals",
        "carried_rows",
        "resources_other",
        "principals_other",
        "resources_other_distinct",
        "role_keys_forced",
        "windows_skipped",
        "requests",
        "reads",
        "writes",
        "errors",
        "response_bytes",
        "last_read_bytes",
        "last_write_bytes",
        "http_status",
        "response_size",
    }
)

#: `partial_window` is the string "true"/"false", NOT a boolean (review #1).
#: `{"term": {"partial_window": true}}` matches nothing. Kept as a constant so
#: the mistake is not retyped.
PARTIAL_TRUE = "true"
PARTIAL_FALSE = "false"


#: Field names learned from the LIVE mapping, populated by `use_mapping()`.
#:
#: WHY THIS EXISTS. `kw()` used to assume every string field was dynamic-mapped
#: as text + `.keyword`. Run 1789007773 measured otherwise: `window_start` is an
#: RFC3339 string, OpenSearch DATE-DETECTS it, and `window_start.keyword` does
#: not exist. So every window-scoped report query matched nothing and eight
#: gates went VOID on an empty result set -- while `min_record_time`, the same
#: shape of value, IS text, because the Lua writes "" on idle windows and the
#: index typed the field from the first one it saw.
#:
#: Two fields, same value shape, different mappings, in one index. Nothing can
#: be assumed here; it has to be read. The builders stay pure functions, so the
#: resolved names live in module state rather than being threaded through nine
#: signatures -- and `use_mapping()` is the only thing that writes it.
_RESOLVED = {}

#: What a mapped type means for exact matching.
_EXACT_AS_IS = frozenset(
    {
        "date",
        "keyword",
        "boolean",
        "long",
        "integer",
        "short",
        "byte",
        "double",
        "float",
        "half_float",
        "scaled_float",
        "unsigned_long",
        "ip",
    }
)


def use_mapping(types):
    """Teach `kw()` the real field names, from `{field: mapped_type}`.

    A field mapped `text` needs `.keyword`; a `date` or a `keyword` is already
    exact-matchable and appending the suffix would match NOTHING -- which is the
    same defect in the opposite direction, and the one that voided run
    1789007773's gates.

    A field whose type is None (nothing has carried it yet) is left to the
    STRING_FIELDS default: absence is not evidence.
    """
    _RESOLVED.clear()
    for field, mapped in (types or {}).items():
        if mapped is None:
            continue
        _RESOLVED[field] = field if mapped in _EXACT_AS_IS else f"{field}.keyword"
    return dict(_RESOLVED)


def resolved_names():
    """What `kw()` will actually emit, for printing at preflight."""
    return dict(_RESOLVED)


def flatten(record, prefix="", out=None):
    """Nested `_source` -> dotted keys, the shape every `log_coverage` helper expects.

    WHY THIS IS NOT COSMETIC. VictoriaLogs flattens nested JSON on ingest, so a
    record arrives as `{"mdc.requestId": "nb-...", "exception.frames": [...]}`.
    OpenSearch keeps the nesting in `_source`: the same record is
    `{"mdc": {"requestId": "nb-..."}, "exception": {"frames": [...]}}`. QUERIES
    are unaffected -- `mdc.requestId` addresses the nested field either way,
    which is why correlation reported 286/286 -- but `record.get("mdc.requestId")`
    returns None on the OpenSearch shape.

    Run 1789008899 hit exactly that: `lc.error_record_pair` filters records by
    `r.get("mdc.requestId")`, matched nothing, and every one of the eight 500s
    came back `absent` -- which reads as "the pipeline dropped the application
    line", a SERIOUS finding, and is a dict access. `lc.exception_fields` has
    the same shape problem and says so in its own docstring: the payload is
    stored FLATTENED as `exception.frames`, and that is true of VictoriaLogs and
    false here.

    So flattening happens once, at this boundary, and the helpers stay unchanged.
    """
    out = {} if out is None else out
    for key, value in (record or {}).items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            flatten(value, f"{name}.", out)
        else:
            out[name] = value
    return out


class MappingFault(RuntimeError):
    """A field is typed in a way that makes the query it is used in a lie."""


def kw(field):
    """Return the aggregatable/term-exact name for `field`.

    Anything in STRING_FIELDS gets `.keyword`; numerics are returned unchanged.
    An unknown field is left alone rather than guessed at -- a wrong suffix
    produces a clean "no such field" rather than a silent zero.
    """
    if field.endswith(".keyword"):
        return field
    if field in _RESOLVED:
        return _RESOLVED[field]
    return f"{field}.keyword" if field in STRING_FIELDS else field


class Metric:
    """A `sum` and the `value_count` that says whether it means anything.

    `value` is None when no document carried the field. That is the whole
    reason this class exists: `sum` over an absent field is 0.0, and a gate
    that reads it as a zero reports a pass for a measurement nobody took.
    """

    __slots__ = ("field", "_sum", "count")

    def __init__(self, field, total, count):
        self.field = field
        self._sum = total
        self.count = int(count or 0)

    @property
    def absent(self):
        return self.count == 0

    @property
    def value(self):
        return None if self.absent else self._sum

    def as_int(self, default=None):
        return default if self.absent else int(self._sum)

    def __repr__(self):
        if self.absent:
            return f"<Metric {self.field} ABSENT (0 docs carried it)>"
        return f"<Metric {self.field}={self._sum:g} over {self.count} doc(s)>"

    def __eq__(self, other):  # so a test can say `m == 26`
        if isinstance(other, Metric):
            return (self.field, self._sum, self.count) == (
                other.field,
                other._sum,
                other.count,
            )
        return (not self.absent) and self._sum == other


class Result:
    """A response, plus when it was taken.

    The timestamp is not decoration. Two counts over a continuously written
    index differ by elapsed time, and without `taken_at` that difference reads
    as missing data -- which is exactly how 2026-09-10 nearly produced a
    finding about 55 rows that were never lost.
    """

    __slots__ = ("body", "taken_at", "index")

    def __init__(self, body, index, taken_at=None):
        self.body = body
        self.index = index
        self.taken_at = taken_at or _dt.datetime.now(_dt.timezone.utc)

    @property
    def total(self):
        t = (self.body.get("hits") or {}).get("total")
        return t.get("value") if isinstance(t, dict) else t

    @property
    def sources(self):
        """Hits as FLATTENED dicts -- see `flatten`. Every consumer of these
        records (log_coverage.error_record_pair, exception_fields,
        check_invariants) was written against VictoriaLogs' flattened shape,
        and a nested `_source` silently reads as an absent field."""
        return [
            flatten(h.get("_source", {}))
            for h in (self.body.get("hits") or {}).get("hits", [])
        ]

    @property
    def raw_sources(self):
        """Hits exactly as OpenSearch returned them. For printing evidence about
        the shape itself -- never for a lookup."""
        return [
            h.get("_source", {}) for h in (self.body.get("hits") or {}).get("hits", [])
        ]

    @property
    def aggs(self):
        return self.body.get("aggregations") or {}

    def __repr__(self):
        return f"<Result {self.index} total={self.total} at {self.taken_at:%H:%M:%SZ}>"


# ----------------------------------------------------------------------
# pure query builders -- no client, no network, fully unit-testable
# ----------------------------------------------------------------------
def v3_filter(schema_version=SCHEMA_VERSION):
    return {"term": {"schema_version": schema_version}}


def window_filter(start=None, end=None, field="window_start"):
    """A range over `window_start` -- the run's own windows, not the index.

    `window_start` is a STRING in the schema (RFC3339), so this is a lexical
    range. RFC3339 with a fixed `Z` offset sorts lexically in time order, which
    is why it works; a mixed-offset timestamp would not, and the filter would
    quietly drop rows.
    """
    rng = {}
    if start is not None:
        rng["gte"] = _iso(start)
    if end is not None:
        rng["lte"] = _iso(end)
    if not rng:
        return None
    return {"range": {kw(field): rng}}


def _filters(*extra, schema_version=SCHEMA_VERSION, window=None):
    """Every report query's filter list. v3 first, always."""
    out = [v3_filter(schema_version)]
    if window is not None:
        wf = window_filter(*window) if isinstance(window, (tuple, list)) else window
        if wf:
            out.append(wf)
    out.extend(f for f in extra if f)
    return out


def q_reports(
    report_type=None,
    window_start=None,
    window=None,
    size=100,
    schema_version=SCHEMA_VERSION,
    source=None,
):
    """Rows, newest first."""
    extra = []
    if report_type:
        extra.append({"term": {kw("report_type"): report_type}})
    if window_start:
        extra.append({"term": {kw("window_start"): _iso(window_start)}})
    body = {
        "size": size,
        "query": {
            "bool": {
                "filter": _filters(*extra, schema_version=schema_version, window=window)
            }
        },
        "sort": [{"@timestamp": "desc"}],
    }
    if source:
        body["_source"] = list(source)
    return body


def q_report_types(window_start=None, window=None, schema_version=SCHEMA_VERSION):
    """Gate 0b: does Fluent Bit's array split into three record types here?"""
    extra = [{"term": {kw("window_start"): _iso(window_start)}}] if window_start else []
    return {
        "size": 0,
        "query": {
            "bool": {
                "filter": _filters(*extra, schema_version=schema_version, window=window)
            }
        },
        "aggs": {"by_type": {"terms": {"field": kw("report_type"), "size": 10}}},
    }


def q_margins(window, size=200, schema_version=SCHEMA_VERSION):
    """Gate 1, in ONE query.

    `sum(resource.requests) == sum(principal.requests) == access_seen -
    parse_errors`, per window. Both margins and both summary counters come back
    from the same response, so they cannot drift apart by elapsed time -- the
    rule §10 of the plan makes binding.

    Every `sum` is accompanied by its `value_count`; `parse_margins` refuses to
    turn an absent field into a zero.
    """

    def _metric(field):
        return {
            f"{field}__sum": {"sum": {"field": field}},
            f"{field}__n": {"value_count": {"field": field}},
        }

    per_type = {}
    for f in (
        "requests",
        "errors",
        "errors_4xx",
        "errors_5xx",
        "auth_denied",
        "response_bytes",
    ):
        per_type.update(_metric(f))
    summary = {}
    for f in (
        "access_seen",
        "parse_errors",
        "access_kept",
        "access_counted",
        "errors_kept",
        "carried_rows",
        "distinct_resources",
        "distinct_principals",
        "role_keys_forced",
        "resources_other",
    ):
        summary.update(_metric(f))

    return {
        "size": 0,
        "query": {
            "bool": {"filter": _filters(schema_version=schema_version, window=window)}
        },
        "aggs": {
            "by_win": {
                "terms": {
                    "field": kw("window_start"),
                    "size": size,
                    "order": {"_key": "asc"},
                },
                "aggs": {
                    "by_type": {
                        "terms": {"field": kw("report_type"), "size": 5},
                        "aggs": per_type,
                    },
                    **summary,
                },
            }
        },
    }


def q_last_write(
    resource=None, kind="table", window=None, size=20, schema_version=SCHEMA_VERSION
):
    """Gate 2 -- THE FEATURE. Rows that claim a `last_write_bytes`."""
    extra = [
        {"term": {kw("report_type"): "resource"}},
        {"exists": {"field": "last_write_bytes"}},
    ]
    if kind:
        extra.append({"term": {kw("resource_kind"): kind}})
    if resource:
        extra.append({"term": {kw("resource"): resource}})
    return {
        "size": size,
        "query": {
            "bool": {
                "filter": _filters(*extra, schema_version=schema_version, window=window)
            }
        },
        "sort": [{"@timestamp": "desc"}],
        "_source": [
            "window_start",
            "window_end",
            "resource",
            "resource_kind",
            "last_write_bytes",
            "last_read_bytes",
            "writes",
            "reads",
        ],
    }


def q_absent_last_write(resource, window, schema_version=SCHEMA_VERSION):
    """Gate 2's negative half: the window whose only write was a DELETE.

    `must_not exists` -- because the assertion is ABSENT, not 0, and a query
    that looks for `last_write_bytes: 0` would pass on a schema that wrote the
    zero the schema forbids.
    """
    return {
        "size": 5,
        "query": {
            "bool": {
                "filter": _filters(
                    {"term": {kw("report_type"): "resource"}},
                    {"term": {kw("resource"): resource}},
                    schema_version=schema_version,
                    window=window,
                ),
                "must_not": [{"exists": {"field": "last_write_bytes"}}],
            }
        },
        "_source": ["window_start", "resource", "writes", "last_write_bytes"],
    }


def q_access_records(
    window_start=None,
    window_end=None,
    method=None,
    path_wildcard=None,
    status=None,
    size=20,
):
    """The `polaris-logs-*` side: the records a report row should have come from.

    No schema_version here -- access-log records do not carry one. That is why
    this builder is named for the other index and takes no `schema_version`
    argument: a caller cannot accidentally pass one and believe it filtered.
    """
    filt = []
    if method:
        filt.append({"term": {kw("http_method"): method}})
    if path_wildcard:
        filt.append({"wildcard": {kw("api_path"): path_wildcard}})
    if status is not None:
        filt.append({"term": {"http_status": status}})
    if window_start or window_end:
        rng = {}
        if window_start:
            rng["gte"] = _iso(window_start)
        if window_end:
            rng["lt"] = _iso(window_end)
        filt.append({"range": {"@timestamp": rng}})
    return {
        "size": size,
        "query": {"bool": {"filter": filt}} if filt else {"match_all": {}},
        "sort": [{"@timestamp": "desc"}],
        "_source": [
            "@timestamp",
            "api_path",
            "http_method",
            "http_status",
            "response_size",
            "mdc.requestId",
            "user_principal_name",
        ],
    }


def q_classification(window=None, schema_version=SCHEMA_VERSION):
    """Gate 3: `api_kind` x `resource_kind`."""
    return {
        "size": 0,
        "query": {
            "bool": {
                "filter": _filters(
                    {"term": {kw("report_type"): "resource"}},
                    schema_version=schema_version,
                    window=window,
                )
            }
        },
        "aggs": {
            "api": {
                "terms": {"field": kw("api_kind"), "size": 10},
                "aggs": {"kind": {"terms": {"field": kw("resource_kind"), "size": 20}}},
            }
        },
    }


def q_role_rows(
    kind="catalog-role", window=None, size=20, schema_version=SCHEMA_VERSION
):
    """Gate 4: `writes` on a catalog-role row is the privilege count."""
    return {
        "size": size,
        "query": {
            "bool": {
                "filter": _filters(
                    {"term": {kw("resource_kind"): kind}},
                    schema_version=schema_version,
                    window=window,
                )
            }
        },
        "sort": [{"@timestamp": "desc"}],
        "_source": [
            "window_start",
            "resource",
            "resource_kind",
            "api_kind",
            "requests",
            "reads",
            "writes",
            "errors",
            "auth_denied",
        ],
    }


def q_synthetic_split(window=None, schema_version=SCHEMA_VERSION):
    """Gate 5: `__errors__` and `__other__` must mean different things.

    The guide writes these terms without `.keyword`. On a dynamic-mapped index
    that runs against the analysed field, where `__errors__` has already become
    the token `errors` -- so the filter matches nothing and the gate passes
    without looking. `kw()` is the fix and `assert_keyword_ready()` proves it.
    """
    return {
        "size": 0,
        "query": {
            "bool": {"filter": _filters(schema_version=schema_version, window=window)}
        },
        "aggs": {
            "synthetic": {
                "filters": {
                    "filters": {
                        "errors": {"term": {kw("resource"): ERRORS_KEY}},
                        "other": {"term": {kw("resource"): OTHER_KEY}},
                    }
                },
                "aggs": {
                    "requests__sum": {"sum": {"field": "requests"}},
                    "requests__n": {"value_count": {"field": "requests"}},
                    "errors__sum": {"sum": {"field": "errors"}},
                    "errors__n": {"value_count": {"field": "errors"}},
                },
            }
        },
    }


def q_unclassified(window=None, schema_version=SCHEMA_VERSION, size=50):
    """Gate 6: a real path with no RESOURCE_PATTERNS rule keeps its own row."""
    return {
        "size": 0,
        "query": {
            "bool": {
                "filter": _filters(
                    {"term": {kw("resource_kind"): "other"}},
                    {"range": {"requests": {"gt": 0}}},
                    schema_version=schema_version,
                    window=window,
                )
            }
        },
        "aggs": {
            "by_api": {
                "terms": {"field": kw("api_kind"), "size": 10},
                "aggs": {"paths": {"terms": {"field": kw("resource"), "size": size}}},
            }
        },
    }


# ----------------------------------------------------------------------
# pure parsers
# ----------------------------------------------------------------------
def metric_of(bucket, field):
    """Pull a `Metric` out of a bucket built by the `_metric` convention."""
    return Metric(
        field,
        (bucket.get(f"{field}__sum") or {}).get("value", 0.0),
        (bucket.get(f"{field}__n") or {}).get("value", 0),
    )


def parse_margins(response):
    """One dict per window: both margins, the summary counters, and the verdict.

    `ok` is None -- not False -- when a window carries no v3 rows at all. An
    unproven check is not a failed one, and reporting it as a failure is how a
    quiet window turns into a phantom pipeline fault.
    """
    aggs = response.get("aggregations") or response
    out = []
    for b in (aggs.get("by_win") or {}).get("buckets") or []:
        by_type = {t["key"]: t for t in ((b.get("by_type") or {}).get("buckets") or [])}
        res = metric_of(by_type.get("resource", {}), "requests")
        pri = metric_of(by_type.get("principal", {}), "requests")
        seen = metric_of(b, "access_seen")
        parse = metric_of(b, "parse_errors")
        row = {
            "window_start": b["key"],
            "rows": b.get("doc_count"),
            "resource_requests": res,
            "principal_requests": pri,
            "access_seen": seen,
            "parse_errors": parse,
            "expected": None if seen.absent else seen.as_int() - parse.as_int(0),
        }
        if res.absent and pri.absent:
            row["ok"], row["why"] = None, "no v3 resource/principal rows in this window"
        elif row["expected"] is None:
            row["ok"], row["why"] = None, "no summary row carried access_seen"
        else:
            row["ok"] = res.as_int(0) == pri.as_int(0) == row["expected"]
            row["why"] = (
                ""
                if row["ok"]
                else (
                    f"resource={res.as_int(0)} principal={pri.as_int(0)} "
                    f"access_seen-parse_errors={row['expected']}"
                )
            )
        for f in (
            "errors_4xx",
            "errors_5xx",
            "auth_denied",
            "carried_rows",
            "distinct_resources",
            "distinct_principals",
            "role_keys_forced",
            "resources_other",
        ):
            row[f] = (
                metric_of(b, f)
                if f
                in (
                    "carried_rows",
                    "distinct_resources",
                    "distinct_principals",
                    "role_keys_forced",
                    "resources_other",
                )
                else metric_of(by_type.get("resource", {}), f)
            )
        out.append(row)
    return out


def parse_synthetic(response):
    """Gate 5's verdict. `__errors__` holds nothing but errors; `__other__` is
    absent or zero unless a window really carried 500+ distinct resources."""
    buckets = ((response.get("aggregations") or {}).get("synthetic") or {}).get(
        "buckets"
    ) or {}
    out = {}
    for name in ("errors", "other"):
        b = buckets.get(name) or {}
        out[name] = {
            "rows": b.get("doc_count", 0),
            "requests": metric_of(b, "requests"),
            "errors": metric_of(b, "errors"),
        }
    e = out["errors"]
    if e["rows"] == 0:
        out["verdict"], out["why"] = (
            None,
            "__errors__ has no rows in this scope -- unproven",
        )
    elif e["requests"].absent or e["errors"].absent:
        out["verdict"], out["why"] = (
            None,
            "__errors__ rows carry no requests/errors field",
        )
    else:
        same = e["requests"].as_int() == e["errors"].as_int()
        out["verdict"] = same
        out["why"] = (
            ""
            if same
            else (
                f"__errors__ holds non-error traffic: requests={e['requests'].as_int()} "
                f"errors={e['errors'].as_int()}"
            )
        )
    return out


def parse_types(response):
    b = ((response.get("aggregations") or {}).get("by_type") or {}).get("buckets") or []
    return {x["key"]: x["doc_count"] for x in b}


def unclassified_paths(response, exclude=SYNTHETIC_KEYS):
    """Gate 6: the real paths behind `resource_kind: other`, synthetic keys removed."""
    out = []
    for api in ((response.get("aggregations") or {}).get("by_api") or {}).get(
        "buckets"
    ) or []:
        for p in (api.get("paths") or {}).get("buckets") or []:
            if p["key"] not in exclude:
                out.append(
                    {
                        "api_kind": api["key"],
                        "resource": p["key"],
                        "rows": p["doc_count"],
                    }
                )
    return out


def _iso(when):
    if isinstance(when, str):
        return when
    if isinstance(when, (int, float)):
        when = _dt.datetime.fromtimestamp(when, _dt.timezone.utc)
    return when.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def window_bounds(when, seconds):
    """The wall-clock-aligned window `when` falls in, as (start, end) ISO Z."""
    epoch = when if isinstance(when, (int, float)) else when.timestamp()
    lo = int(epoch // seconds) * seconds
    return _iso(lo), _iso(lo + seconds)


def seconds_to_boundary(window_seconds, lag=0.0, now=None):
    now = _time.time() if now is None else now
    return (window_seconds - (now % window_seconds)) + lag


# ----------------------------------------------------------------------
# the client
# ----------------------------------------------------------------------
class OSReports:
    """One OpenSearch instance, two indices, every guard above applied.

    Credentials come from the caller (`init_env` -> `OPENSEARCH_*`), never from
    this module.
    """

    def __init__(
        self,
        base_url,
        auth=None,
        report_index=DEFAULT_REPORT_INDEX,
        logs_index=DEFAULT_LOGS_INDEX,
        schema_version=SCHEMA_VERSION,
        verify=False,
        timeout=DEFAULT_TIMEOUT,
        session=None,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.auth = auth
        self.report_index = report_index
        self.logs_index = logs_index
        self.schema_version = schema_version
        self.verify = verify
        self.timeout = timeout
        self.session = session or requests.Session()

    # -- low level -----------------------------------------------------
    def raw_search(self, index, body):
        """Unguarded. Named so it is conspicuous in a diff -- a report query
        that goes through here has no schema_version filter unless the caller
        wrote one, which is the whole failure this module exists to prevent."""
        r = self.session.post(
            f"{self.base_url}/{index}/_search",
            json=body,
            auth=self.auth,
            verify=self.verify,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return Result(r.json(), index)

    def report(self, body):
        return self.raw_search(self.report_index, body)

    def logs(self, body):
        return self.raw_search(self.logs_index, body)

    def ping(self):
        try:
            r = self.session.get(
                self.base_url, auth=self.auth, verify=self.verify, timeout=8
            )
            v = (r.json() or {}).get("version") or {}
            return (
                r.status_code < 500,
                f"HTTP {r.status_code} {v.get('distribution','')} {v.get('number','')}".strip(),
            )
        except Exception as exc:  # noqa: BLE001
            return (False, f"{type(exc).__name__}: {exc}")

    def indices(self, pattern="polaris-*"):
        r = self.session.get(
            f"{self.base_url}/_cat/indices/{pattern}",
            params={"h": "index,docs.count,store.size", "format": "json"},
            auth=self.auth,
            verify=self.verify,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def mapping_of(self, field, index=None):
        """The mapped type of `field`, or None if nothing has carried it.

        This is how the `min_record_time` trap is caught BEFORE a gate leans on
        it: the Lua writes "" on idle windows, OpenSearch types the field from
        the first document, and that typing is permanent for the index.
        """
        index = index or self.report_index
        r = self.session.get(
            f"{self.base_url}/{index}/_mapping/field/{field}",
            auth=self.auth,
            verify=self.verify,
            timeout=self.timeout,
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return _first_type(r.json())

    def field_types(self, fields, index=None):
        """{field: mapped type or None} for many fields, in ONE request."""
        index = index or self.report_index
        wanted = list(fields)
        r = self.session.get(
            f"{self.base_url}/{index}/_mapping/field/{','.join(wanted)}",
            auth=self.auth,
            verify=self.verify,
            timeout=self.timeout,
        )
        if r.status_code == 404:
            return {f: None for f in wanted}
        r.raise_for_status()
        found = _types_of(r.json())
        return {f: found.get(f) for f in wanted}

    def learn_field_names(self, index=None, fields=None):
        """Read the live mapping and teach `kw()` the real names.

        Call this at preflight, before any query is built. Returns
        {field: name kw() will emit} so the notebook can print it -- the
        resolution is a measurement and belongs in the record.
        """
        fields = list(fields or sorted(STRING_FIELDS))
        types = self.field_types(fields, index)
        use_mapping(types)
        return {f: kw(f) for f in fields}, types

    # -- the checks a run must pass before it trusts its own numbers ----
    def assert_numeric(
        self, fields=("requests", "errors", "response_bytes"), index=None
    ):
        """Raise unless every field is mapped as a number.

        A text-typed `requests` makes every `sum` in gates 1-5 wrong while
        every query still returns 200. Fail loudly, at preflight, once.
        """
        bad = {}
        for f in fields:
            t = self.mapping_of(f, index)
            if t is None:
                bad[f] = "not mapped (no document has carried it)"
            elif t not in (
                "long",
                "integer",
                "short",
                "double",
                "float",
                "half_float",
                "scaled_float",
                "unsigned_long",
            ):
                bad[f] = t
        if bad:
            raise MappingFault(
                "report fields are not numeric in "
                f"{index or self.report_index}: {bad}. Every sum over these is "
                "meaningless; fix the index template before taking a measurement."
            )
        return True

    def assert_keyword_ready(
        self, fields=("resource", "report_type", "window_start"), index=None
    ):
        """Raise unless each string field has an exact-match `.keyword` subfield.

        Without it `{"term": {"resource": "__errors__"}}` matches nothing and
        Gate 5 passes without looking.
        """
        types = self.field_types(list(fields), index)
        missing = []
        for f, mapped in types.items():
            if mapped in _EXACT_AS_IS or mapped is None:
                continue  # date/keyword match exactly as they are; None = unmapped
            if self.mapping_of(f"{f}.keyword", index) is None:
                missing.append(f)
        if missing:
            raise MappingFault(
                f"text field(s) {missing} in {index or self.report_index} have no "
                ".keyword subfield: exact-match term filters on them silently match "
                "nothing."
            )
        return True

    # -- report queries ------------------------------------------------
    def reports(self, **kw_):
        return self.report(q_reports(schema_version=self.schema_version, **kw_))

    def report_types(self, window_start=None, window=None):
        return parse_types(
            self.report(q_report_types(window_start, window, self.schema_version)).body
        )

    def margins(self, window):
        """Gate 1, one query, both margins and the summary counters together."""
        return parse_margins(
            self.report(q_margins(window, schema_version=self.schema_version)).body
        )

    def synthetic_split(self, window=None):
        return parse_synthetic(
            self.report(q_synthetic_split(window, self.schema_version)).body
        )

    def unclassified(self, window=None):
        return unclassified_paths(
            self.report(q_unclassified(window, self.schema_version)).body
        )

    def latest_summary(self, with_traffic=False, window=None):
        body = q_reports(
            report_type="summary",
            window=window,
            size=1,
            schema_version=self.schema_version,
        )
        if with_traffic:
            body["query"]["bool"]["filter"].append(
                {"range": {"access_seen": {"gt": 0}}}
            )
        rows = self.report(body).sources
        return rows[0] if rows else None

    # -- the logs side -------------------------------------------------
    def for_request_id(self, request_id, size=50):
        return self.logs(
            {
                "size": size,
                "query": {
                    "bool": {"filter": [{"term": {kw("mdc.requestId"): request_id}}]}
                },
                "sort": [{"@timestamp": "asc"}],
            }
        ).sources

    def status_mix(self, window_start=None, window_end=None, size=20):
        body = q_access_records(window_start, window_end, size=0)
        body["aggs"] = {"s": {"terms": {"field": "http_status", "size": size}}}
        r = self.logs(body)
        return {
            b["key"]: b["doc_count"]
            for b in ((r.aggs.get("s") or {}).get("buckets") or [])
        }

    def settle(self, body, index=None, quiet_for=4.0, timeout=90.0, interval=2.0):
        """Poll until the hit count stops moving. Ingest is asynchronous, so a
        count taken too early is a statement about the clock, not the pipeline."""
        index = index or self.report_index
        t0, last, stable_since = _time.time(), None, None
        res = None
        while _time.time() - t0 < timeout:
            res = self.raw_search(index, body)
            n = res.total
            if n == last and n:
                if stable_since is None:
                    stable_since = _time.time()
                elif _time.time() - stable_since >= quiet_for:
                    return res
            else:
                last, stable_since = n, None
            _time.sleep(interval)
        return res


def _types_of(mapping_response):
    """{full_name: mapped type} from a `_mapping/field/a,b,c` response.

    `_first_type` walks the whole document and returns the first `type` it
    meets, which is correct for one field and silently wrong for many -- every
    field would come back as whichever one OpenSearch serialised first.
    """
    out = {}
    for index_body in (mapping_response or {}).values():
        for name, body in ((index_body or {}).get("mappings") or {}).items():
            leaf = (body or {}).get("mapping") or {}
            for _, spec in leaf.items():
                t = (spec or {}).get("type")
                if isinstance(t, str):
                    out.setdefault((body or {}).get("full_name", name), t)
    return out


def _first_type(mapping_response):
    """Walk a _mapping/field response for the first `type` it names."""
    stack = [mapping_response]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "type" in node and isinstance(node["type"], str):
                return node["type"]
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None
