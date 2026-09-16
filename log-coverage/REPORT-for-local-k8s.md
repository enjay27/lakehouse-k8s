# For `local-k8s`: what this run says needs changing there

Produced by `log-coverage/polaris_log_coverage_v2.ipynb`, run 1789436277, 2026-09-15 01:41Z.
Only items whose fix lives in the pipeline repo are here; everything else stays in
`doc-api-status-matrix-results.md`.





**How it was driven:** 63 operations from the vendored OpenAPI documents, 286 (operation x status) cells, boundary-aligned phases so the per-window gates mean something.

## Build findings -- POLARIS facts, NOT `local-k8s` work

Here only because this run provoked them. Nothing in this section is a change for the pipeline repo.

### 4 response(s) of 500 in this run

**Measured:** getToken (target 400, as runner); createNamespace (target 400, as runner); renameTable (target 400, as runner); renameView (target 400, as runner)   trace verdicts: ['unhandled']

**Note:** these are reachable through the API alone, with no cluster surgery -- which answers the standing question in .memory/roadmap.md about provoking an unhandled exception. `errors_5xx` can now be exercised on demand. UNHANDLED (a throwable survived): ['getToken@400', 'createNamespace@400', 'renameTable@400', 'renameView@400'].

## For `GUIDE-schema-v3-testing.md` itself

### Gate 5's term filter should read resource.keyword

**Measured:** GUIDE-schema-v3-testing.md Gate 5 uses {"term": {"resource": "__errors__"}}, which on a dynamic-mapped index runs against the ANALYSED text field. NOT SETTLED HERE: the guide says the analyser splits __errors__ into `errors`; underscore is ExtendNumLet under UAX#29, so StandardTokenizer should emit it whole, and this run's own Gate 5 returned requests=68 over 4 doc(s) rather than nothing. One call settles it: GET polaris-report-*/_analyze {"field": "resource", "text": "__errors__"}.

**Change:** use resource.keyword regardless (Gate 2's resource_kind filter has the same shape). The mechanism above is disputed; the case-folding one is not -- analysis lowercases, so a term query for POST matches nothing while POST.keyword matches. Settle the _analyze question before the wrong mechanism propagates into another document.
