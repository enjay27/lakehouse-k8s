# API status matrix -- run 1789370776

Driven 2026-09-14 07:29Z against `local`, schema v3, windows of 30s.

> **WINDOWS.** Window attribution is INCONSISTENT across rows ({-30: 5, 0: 1}); no single offset can correct it, so window-scoped gates were read unshifted and must not be quoted.



- **63 operations**, **286 cells**, 286 calls issued
- covered: 228   missed: 58   transport errors: 0
- correlation on error cells (rule 3, an assertion): 235/235
- 500 ladder: NOT PROVOKED (expected on this build)   |   500s anywhere in the run: 4 (createNamespace, getToken, renameTable, renameView)

## Gates

| gate | verdict | detail |
|---|---|---|
| Gate 1 margins | PASS | 6/6 windows answered |
| Gate 0b array split | PASS | {'resource': 135, 'principal': 18, 'summary': 6} |
| Gate 2 last_write_bytes | VOID | 2 table row(s) in this window and none carries last_write_bytes. THIS SAYS NOTHING ABOUT WHETHER THE FEATURE WORKS: the OpenSearch export of 2026-09-14 shows last_write_bytes and last_read_bytes firing wherever a sized write or read occurred (last write 536 / 117, last read 53) and absent exactly where the response was 0 bytes, which is the `> 0` guard working. A VOID here means this window held no sized table write -- check WHICH window was read before blaming the filter |
| Gate 2 delete leaves it ABSENT | VOID | rows without the field=0  rows WITH it=0 (want 0) |
| Gate 3 classification | PASS | {'management': ['collection', 'principal-role', 'catalog-role', 'principal', 'catalog'], 'catalog': ['collection', 'table', 'namespace', 'view', 'auth', 'config', 'transaction'], 'mixed': ['error']} |
| Gate 4 privilege count | FAIL | writes=1 granted=3 on /api/management/v1/catalogs/apimatrix1789370776_cat/catalog-roles/mx_1789370776_crole |
| Gate 4 denial forces the row | FAIL | auth_denied=0 (the ROLE_KINDS exemption; 0 means the 403 fell to __errors__) |
| Gate 4 grants fold into the role | PASS | no separate grants row |
| Gate 5 __errors__ holds only errors | PASS | requests=<Metric requests=68 over 4 doc(s)> |
| Gate 5 __other__ is overflow only | VOID | __other__ requests=<Metric requests ABSENT (0 docs carried it)> -- non-zero means a window really carried 500+ distinct resources, or the split regressed |
| Gate 6 every path has a rule | PASS | only the synthetic keys came back, over 135 resource row(s) |

## Windows

| phase | start | seconds | cells | straddled |
|---|---|---|---|---|
| B | 2026-09-14T07:26:30Z | 1.0 | 63 | False |
| C | 2026-09-14T07:27:00Z | 1.0 | 180 | False |
| D | 2026-09-14T07:27:30Z | 0.5 | 43 | False |
| E | 2026-09-14T07:28:00Z | 0.1 | 1 | False |
| F | 2026-09-14T07:28:30Z | 0.0 | 1 | False |
| G | 2026-09-14T07:29:00Z | 0.1 | 4 | False |
| H | 2026-09-14T07:29:30Z | 0.6 | 12 | False |

## Coverage by operation

| op_id | method | api | covered | missed | not_driven | declared |
|---|---|---|---|---|---|---|
| getConfig | GET | catalog | [2, 400, 401] | [403] | [] | ('200', '400', '401', '403', '419', '503', '5XX') |
| getToken | POST | catalog | [2, 401] | [400] | [] | ('200', '400', '401', '5XX') |
| listNamespaces | GET | catalog | [2, 401, 403, 404] | [] | [] | ('200', '400', '401', '403', '404', '419', '503', '5XX') |
| createNamespace | POST | catalog | [2, 401, 403, 404, 409] | [400] | [] | ('200', '400', '401', '403', '406', '409', '419', '503', '5XX') |
| dropNamespace | DELETE | catalog | [2, 401, 404] | [403, 409] | [] | ('204', '400', '401', '403', '404', '409', '419', '503', '5XX') |
| loadNamespaceMetadata | GET | catalog | [2, 401, 403, 404] | [] | [] | ('200', '400', '401', '403', '404', '419', '503', '5XX') |
| namespaceExists | HEAD | catalog | [2, 401, 403, 404] | [] | [] | ('204', '400', '401', '403', '404', '419', '503', '5XX') |
| updateProperties | POST | catalog | [2, 400, 401, 403, 404] | [] | [] | ('200', '400', '401', '403', '404', '406', '419', '422', '503', '5XX') |
| registerTable | POST | catalog | [400, 401, 403, 404] | [2, 409] | [] | ('200', '400', '401', '403', '404', '409', '419', '503', '5XX') |
| listTables | GET | catalog | [2, 401, 403, 404] | [] | [] | ('200', '400', '401', '403', '404', '419', '503', '5XX') |
| createTable | POST | catalog | [2, 400, 401, 403, 404] | [409] | [] | ('200', '400', '401', '403', '404', '409', '419', '503', '5XX') |
| dropTable | DELETE | catalog | [2, 401, 404] | [403] | [] | ('204', '400', '401', '403', '404', '419', '503', '5XX') |
| loadTable | GET | catalog | [2, 401, 403, 404] | [] | [] | ('200', '304', '400', '401', '403', '404', '419', '503', '5XX') |
| tableExists | HEAD | catalog | [2, 401, 403, 404] | [] | [] | ('204', '400', '401', '403', '404', '419', '503', '5XX') |
| updateTable | POST | catalog | [2, 401, 403, 404] | [400, 409] | [] | ('200', '400', '401', '403', '404', '409', '419', '500', '502', '503', '504', '5XX') |
| loadCredentials | GET | catalog | [2, 401, 403, 404] | [] | [] | ('200', '400', '401', '403', '404', '419', '503', '5XX') |
| reportMetrics | POST | catalog | [2, 400, 401] | [403, 404] | [] | ('204', '400', '401', '403', '404', '419', '503', '5XX') |
| planTableScan | POST | catalog | [404] | [2, 400, 401, 403] | [] | ('200', '400', '401', '403', '404', '406', '419', '503', '5XX') |
| cancelPlanning | DELETE | catalog | [404] | [2, 401, 403] | [] | ('204', '400', '401', '403', '404', '419', '503', '5XX') |
| fetchPlanningResult | GET | catalog | [404] | [2, 401, 403] | [] | ('200', '400', '401', '403', '404', '419', '503', '5XX') |
| fetchScanTasks | POST | catalog | [404] | [2, 400, 401, 403] | [] | ('200', '400', '401', '403', '404', '419', '503', '5XX') |
| listViews | GET | catalog | [2, 401, 403, 404] | [] | [] | ('200', '400', '401', '403', '404', '419', '503', '5XX') |
| createView | POST | catalog | [2, 400, 401, 403, 404] | [409] | [] | ('200', '400', '401', '403', '404', '409', '419', '503', '5XX') |
| dropView | DELETE | catalog | [2, 401, 404] | [403] | [] | ('204', '400', '401', '403', '404', '419', '503', '5XX') |
| loadView | GET | catalog | [401, 404] | [2, 403] | [] | ('200', '400', '401', '403', '404', '419', '503', '5XX') |
| viewExists | HEAD | catalog | [401, 404] | [2, 403] | [] | ('204', '400', '401', '404', '419', '503', '5XX') |
| replaceView | POST | catalog | [401, 404] | [2, 400, 403, 409] | [] | ('200', '400', '401', '403', '404', '409', '419', '500', '502', '503', '504', '5XX') |
| renameTable | POST | catalog | [401, 404] | [2, 400, 403, 409] | [] | ('204', '400', '401', '403', '404', '406', '409', '419', '503', '5XX') |
| commitTransaction | POST | catalog | [2, 400, 401, 403, 404] | [409] | [] | ('204', '400', '401', '403', '404', '409', '419', '500', '502', '503', '504', '5XX') |
| renameView | POST | catalog | [2, 401, 404, 409] | [400, 403] | [] | ('204', '400', '401', '403', '404', '406', '409', '419', '503', '5XX') |
| listCatalogs | GET | management | [2, 401, 403] | [] | [] | ('200', '403') |
| createCatalog | POST | management | [2, 400, 401, 403, 409] | [] | [] | ('201', '403', '404', '409') |
| deleteCatalog | DELETE | management | [2, 401, 404] | [403] | [] | ('204', '403', '404') |
| getCatalog | GET | management | [2, 401, 403, 404] | [] | [] | ('200', '403', '404') |
| updateCatalog | PUT | management | [2, 400, 401, 403, 404, 409] | [] | [] | ('200', '403', '404', '409') |
| listCatalogRoles | GET | management | [2, 401, 403, 404] | [] | [] | ('200',) |
| createCatalogRole | POST | management | [2, 401, 403, 404] | [400] | [] | ('201', '403', '404') |
| deleteCatalogRole | DELETE | management | [2, 401, 404] | [403] | [] | ('204', '403', '404') |
| getCatalogRole | GET | management | [2, 401, 403, 404] | [] | [] | ('200', '403', '404') |
| updateCatalogRole | PUT | management | [2, 400, 401, 403, 404, 409] | [] | [] | ('200', '403', '404', '409') |
| listGrantsForCatalogRole | GET | management | [2, 401, 403, 404] | [] | [] | ('200',) |
| revokeGrantFromCatalogRole | POST | management | [400, 401, 403, 404] | [2] | [] | ('201', '403', '404') |
| addGrantToCatalogRole | PUT | management | [2, 400, 401, 403, 404] | [] | [] | ('201', '403', '404') |
| listAssigneePrincipalRolesForCatalogRole | GET | management | [2, 401, 403, 404] | [] | [] | ('200', '403', '404') |
| listPrincipalRoles | GET | management | [2, 401, 403] | [] | [] | ('200', '403', '404') |
| createPrincipalRole | POST | management | [2, 401, 403] | [400] | [] | ('201', '403') |
| deletePrincipalRole | DELETE | management | [2, 401, 404] | [403] | [] | ('204', '403', '404') |
| getPrincipalRole | GET | management | [2, 401, 403, 404] | [] | [] | ('200', '403', '404') |
| updatePrincipalRole | PUT | management | [2, 400, 401, 403, 404, 409] | [] | [] | ('200', '403', '404', '409') |
| listCatalogRolesForPrincipalRole | GET | management | [2, 401, 403, 404] | [] | [] | ('200', '403', '404') |
| assignCatalogRoleToPrincipalRole | PUT | management | [2, 401, 403, 404] | [400] | [] | ('201', '403') |
| revokeCatalogRoleFromPrincipalRole | DELETE | management | [401, 404] | [2, 403] | [] | ('204', '403', '404') |
| listAssigneePrincipalsForPrincipalRole | GET | management | [2, 401, 403, 404] | [] | [] | ('200', '403', '404') |
| listPrincipals | GET | management | [2, 401, 403] | [] | [] | ('200', '403', '404') |
| createPrincipal | POST | management | [2, 400, 401, 403] | [] | [] | ('201', '403') |
| deletePrincipal | DELETE | management | [2, 401, 404] | [403] | [] | ('204', '403', '404') |
| getPrincipal | GET | management | [2, 401, 403, 404] | [] | [] | ('200', '403', '404') |
| updatePrincipal | PUT | management | [2, 400, 401, 403, 404, 409] | [] | [] | ('200', '403', '404', '409') |
| listPrincipalRolesAssigned | GET | management | [2, 401, 403, 404] | [] | [] | ('200', '403', '404') |
| assignPrincipalRole | PUT | management | [2, 401, 403, 404] | [400] | [] | ('201', '403', '404') |
| revokePrincipalRole | DELETE | management | [401, 404] | [2, 403] | [] | ('204', '403', '404') |
| resetCredentials | POST | management | [2, 400, 401, 403, 404] | [] | [] | ('200', '403', '404') |
| rotateCredentials | POST | management | [401, 403, 404] | [2] | [] | ('200', '403', '404') |

## Not reachable

| status | state | why |
|---|---|---|
| 304 | probe | needs If-None-Match support on loadTable |
| 406 | probe | needs content negotiation to refuse a JSON-only endpoint |
| 419 | probe | Iceberg's credential-refresh code; this build is expected to answer 401 instead |
| 429 | settled | rateLimiter.type is no-op on this build -- the limiter cannot produce a 429 |
| 502 | settled | nothing proxies Polaris here; a port-forward is not a gateway |
| 503 | settled | the only route is scaling Polaris, and HPA movement invalidates the run (local-k8s #8) |
| 504 | settled | same -- no gateway to time out |
| 5XX | settled | a spec placeholder, not a status |