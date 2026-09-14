# For `local-k8s`: what this run says needs changing there

Produced by `log-coverage/polaris_log_coverage_v2.ipynb`, run 1789365275, 2026-09-14 05:58Z.
Only items whose fix lives in the pipeline repo are here; everything else stays in
`doc-api-status-matrix-results.md`.



**How it was driven:** 63 operations from the vendored OpenAPI documents, 286 (operation x status) cells, boundary-aligned phases so the per-window gates mean something.

## 1. index mapping

**Measured:** min_record_time is text in polaris-report-2026.09.14; the invariant is still checkable client-side (RFC3339 parses), but no range query or date histogram works on it here. Remedy: an index template for polaris-report-* typing min/max_record_time as date.

**Change:** an index template for polaris-report-* typing min_record_time / max_record_time as date, and the numeric report fields as long. A template survives the Lua writing "" on idle windows; waiting for a fresh index does not, because the first window of a day is almost always idle at 30s windows. See the Gate 7 finding above: that empty string is very likely the CAUSE of this mapping rather than an inconvenience beside it, which would make the template a workaround and the filter the fix.

## 2. Gate 4 privilege count FAILED

**Measured:** writes=1 granted=3 on /api/management/v1/catalogs/apimatrix1789365275_cat/catalog-roles/mx_1789365275_crole_doomed

**Change:** see the gate's stated failure mode in GUIDE-schema-v3-testing.md

## 3. Gate 4 denial forces the row FAILED

**Measured:** auth_denied=0 (the ROLE_KINDS exemption; 0 means the 403 fell to __errors__)

**Change:** see the gate's stated failure mode in GUIDE-schema-v3-testing.md

## 4. 4 response(s) of 500 in this run

**Measured:** getToken (target 400, as runner); createNamespace (target 400, as runner); renameTable (target 400, as runner); renameView (target 400, as runner)   trace verdicts: ['unhandled']

**Change:** these are reachable through the API alone, with no cluster surgery -- which answers the standing question in .memory/roadmap.md about provoking an unhandled exception. `errors_5xx` can now be exercised on demand. UNHANDLED (a throwable survived): ['getToken@400', 'createNamespace@400', 'renameTable@400', 'renameView@400'].

## For `GUIDE-schema-v3-testing.md` itself

### Gate 5's term filter matches nothing as written

**Measured:** GUIDE-schema-v3-testing.md Gate 5 uses {"term": {"resource": "__errors__"}}. On a dynamic-mapped index that runs against the analysed text field, where the standard analyser has already turned __errors__ into the token `errors`.

**Change:** use resource.keyword (Gate 2's resource_kind filter has the same shape). Until then that gate reports zero and passes without having looked.
