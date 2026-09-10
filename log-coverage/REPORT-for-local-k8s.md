# For `local-k8s`: what this run says needs changing there

Produced by `log-coverage/polaris_log_coverage_v2.ipynb`, run 1789008333, 2026-09-10 02:49Z.
Only items whose fix lives in the pipeline repo are here; everything else stays in
`doc-api-status-matrix-results.md`.

**How it was driven:** 63 operations from the vendored OpenAPI documents, 286 (operation x status) cells, boundary-aligned phases so the per-window gates mean something.

## 1. index mapping

**Measured:** no .keyword subfield for ['window_start'] in polaris-report-2026.09.10: exact-match term filters on these silently match nothing.

**Change:** an index template for polaris-report-* typing min_record_time / max_record_time as date, and the numeric report fields as long. A template survives the Lua writing "" on idle windows; waiting for a fresh index does not, because the first window of a day is almost always idle at 30s windows.

## 2. index mapping

**Measured:** min_record_time is text in polaris-report-2026.09.10; the invariant is still checkable client-side (RFC3339 parses), but no range query or date histogram works on it here. Remedy: an index template for polaris-report-* typing min/max_record_time as date.

**Change:** an index template for polaris-report-* typing min_record_time / max_record_time as date, and the numeric report fields as long. A template survives the Lua writing "" on idle windows; waiting for a fresh index does not, because the first window of a day is almost always idle at 30s windows.

## For `GUIDE-schema-v3-testing.md` itself

### Gate 5's term filter matches nothing as written

**Measured:** GUIDE-schema-v3-testing.md Gate 5 uses {"term": {"resource": "__errors__"}}. On a dynamic-mapped index that runs against the analysed text field, where the standard analyser has already turned __errors__ into the token `errors`.

**Change:** use resource.keyword (Gate 2's resource_kind filter has the same shape). Until then that gate reports zero and passes without having looked.
