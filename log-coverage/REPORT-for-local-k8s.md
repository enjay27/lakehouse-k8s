# For `local-k8s`: what this run says needs changing there

Produced by `log-coverage/polaris_log_coverage_v2.ipynb`, run 1789370776, 2026-09-14 07:29Z.
Only items whose fix lives in the pipeline repo are here; everything else stays in
`doc-api-status-matrix-results.md`.

> **WINDOWS.** Window attribution is INCONSISTENT across rows ({-30: 5, 0: 1}); no single offset can correct it, so window-scoped gates were read unshifted and must not be quoted.



**How it was driven:** 63 operations from the vendored OpenAPI documents, 286 (operation x status) cells, boundary-aligned phases so the per-window gates mean something.

## 1. invariant FAILED: record times fall INSIDE their own window  **SERIOUS**

**Measured:** 6 window(s) checked; 6 carried a timestamp outside [window_start, window_start+window_seconds]; worst lag 1.569s, e.g. {'window_start': '2026-09-14T07:29:00Z', 'min': '2026-09-14T07:29:30.594786271Z', 'max': '2026-09-14T07:29:31.569180453Z', 'lead_s': -30.595, 'lag_s': 1.569}   -- outside means the window is assigned by PROCESSING time, not record time

**Change:** a report row must be stamped with the window its records fall in. Measured: a row labelled W carries the traffic of W+1 -- window_start 06:52:00Z with min_record_time 06:52:30.573 -- and confirmed independently in the OpenSearch export, where seq=117 (labelled 06:52:00..06:52:30) holds access lines stamped 06:52:31. The offset is NOT constant: measured across rows it is {-30: 5, 0: 1}, so it depends on where in the window the traffic lands and no single shift can correct it downstream. Every per-window number in this report, and every window-scoped gate, is read from the wrong row until this is fixed.

## 2. index mapping

**Measured:** min_record_time is text in polaris-report-2026.09.14; the invariant is still checkable client-side (RFC3339 parses), but no range query or date histogram works on it here. Remedy: an index template for polaris-report-* typing min/max_record_time as date.

**Change:** an index template for polaris-report-* typing min_record_time / max_record_time as date (or date_nanos), and the numeric report fields as long. LIKELY CAUSE, REVISED 2026-09-14 -- not the empty string the earlier note blamed: the same index maps window_start as `date`, and window_start carries NO fractional part while min/max_record_time carry NINE digits (...30.587684196Z). Dynamic date detection declines that, and the field is text for the life of the index. So the options are an explicit mapping or truncating to milliseconds in the filter, and a template alone leaves every future index one such field away from the same thing. Decisive free test: the next day's index is written entirely by the rolled filter.

## Build findings -- POLARIS facts, NOT `local-k8s` work

Here only because this run provoked them. Nothing in this section is a change for the pipeline repo.

### 4 response(s) of 500 in this run

**Measured:** getToken (target 400, as runner); createNamespace (target 400, as runner); renameTable (target 400, as runner); renameView (target 400, as runner)   trace verdicts: ['unhandled']

**Note:** these are reachable through the API alone, with no cluster surgery -- which answers the standing question in .memory/roadmap.md about provoking an unhandled exception. `errors_5xx` can now be exercised on demand. UNHANDLED (a throwable survived): ['getToken@400', 'createNamespace@400', 'renameTable@400', 'renameView@400'].

## For `GUIDE-schema-v3-testing.md` itself

### Gate 5's term filter matches nothing as written

**Measured:** GUIDE-schema-v3-testing.md Gate 5 uses {"term": {"resource": "__errors__"}}. On a dynamic-mapped index that runs against the analysed text field, where the standard analyser has already turned __errors__ into the token `errors`.

**Change:** use resource.keyword (Gate 2's resource_kind filter has the same shape). Until then that gate reports zero and passes without having looked.
