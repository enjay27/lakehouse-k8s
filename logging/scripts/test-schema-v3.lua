-- Regression test for report schema v3, run against the ACTUAL deployed Lua.
--
--   cp fluent-bit/polaris_access_log.lua /tmp/polaris.lua     # the deployed script is its own file since 2026-09-15
--   lua5.4 logging/scripts/test-schema-v3.lua
--
-- Needs a lua interpreter; the Fluent Bit image is distroless and has none, and the
-- Cowork VM has none either -- run it in the cloud container or install lua locally.
--
-- Two things this catches that reading cannot: `%\-` in a Lua pattern is an INVALID
-- ESCAPE and fails the whole chunk at load (caught exactly this way on 2026-09-09),
-- and the startup blind spot means records fed before the FIRST tick are dropped, so a
-- naive harness reports zeros and looks like a broken filter.
dofile("/tmp/polaris.lua")
local T0 = 1788940800   -- aligned to a 30s boundary
local A = "io.quarkus.http.access-log"
local fails = 0
local function check(name, got, want)
  local ok = tostring(got) == tostring(want)
  if not ok then fails = fails + 1 end
  print(string.format("  [%s] %-46s got=%-8s want=%s", ok and "PASS" or "FAIL", name,
                      tostring(got), tostring(want)))
end
local function rec(m,p,st,sz)
  return { loggerName=A, http_method=m, api_path=p, http_status=tostring(st),
           response_size=tostring(sz), user_principal_name="svc",
           _time="2026-09-09T08:00:05.000Z", _now_override=T0+5 }
end

polaris_noise_filter("polaris.report", 0, {tick="x", _now_override=T0+1})  -- opens the window
local CAT="/api/catalog/v1/cat1"
local T = CAT.."/namespaces/ns1/tables/orders"
polaris_noise_filter("polaris.logs", 0, rec("GET",   T, 200, 4812))
polaris_noise_filter("polaris.logs", 0, rec("POST",  T, 200, 5140))  -- the commit
polaris_noise_filter("polaris.logs", 0, rec("GET",   T, 200, 5203))  -- later read wins
polaris_noise_filter("polaris.logs", 0, rec("DELETE",T, 204, 0))     -- empty  -> ignored
polaris_noise_filter("polaris.logs", 0, rec("POST",  T, 500, 999))   -- 5xx    -> ignored
polaris_noise_filter("polaris.logs", 0, rec("HEAD",  T, 200, 0))     -- no body-> ignored
polaris_noise_filter("polaris.logs", 0, rec("POST", CAT.."/tables/rename", 200, 36))
polaris_noise_filter("polaris.logs", 0, rec("POST", CAT.."/views/rename", 200, 12))
polaris_noise_filter("polaris.logs", 0, rec("POST", CAT.."/namespaces/ns1/properties", 200, 43))
-- commitTransaction: a MULTI-table commit, no /namespaces/ segment and no single table
-- identity. It was the one real path the 63-operation API matrix found with no rule
-- (run 1789026666, Gate 6). Its own kind -- folding it into `table` would blur every
-- per-table trend, and the row key is the whole path either way.
polaris_noise_filter("polaris.logs", 0, rec("POST", CAT.."/transactions/commit", 200, 77))
polaris_noise_filter("polaris.logs", 0, rec("POST", "/api/catalog/v1/oauth/tokens", 200, 685))
polaris_noise_filter("polaris.logs", 0, rec("GET",  "/api/catalog/v1/config", 200, 1757))
-- ROLES. Everything under a role folds into that role's row, so the grant count is
-- the row's `writes`. Three grants + one CRUD read on ONE catalog role.
local CR = "/api/management/v1/catalogs/c1/catalog-roles/analyst"
polaris_noise_filter("polaris.logs", 0, rec("PUT", CR.."/grants", 200, 19))
polaris_noise_filter("polaris.logs", 0, rec("PUT", CR.."/grants", 200, 19))
polaris_noise_filter("polaris.logs", 0, rec("PUT", CR.."/grants", 200, 21))
polaris_noise_filter("polaris.logs", 0, rec("GET", CR,            200, 64))
-- a different catalog role stays a different row
polaris_noise_filter("polaris.logs", 0, rec("PUT", "/api/management/v1/catalogs/c1/catalog-roles/reader/grants", 200, 11))
-- principal-role rules win over catalog-role for the assignment path
polaris_noise_filter("polaris.logs", 0, rec("PUT", "/api/management/v1/principal-roles/pr1/catalog-roles/c1", 200, 12))
polaris_noise_filter("polaris.logs", 0, rec("GET", "/api/management/v1/principal-roles/pr1", 200, 55))
-- collections
polaris_noise_filter("polaris.logs", 0, rec("GET", "/api/management/v1/principal-roles", 200, 90))
polaris_noise_filter("polaris.logs", 0, rec("GET", "/api/management/v1/principals/p1/principal-roles", 200, 31))
-- plain principal management is NOT a role
polaris_noise_filter("polaris.logs", 0, rec("GET", "/api/management/v1/principals/p1", 200, 64))
-- a DENIED grant on a role with NO successful request this window. create=false would
-- send it to __other__; ROLE_KINDS lets it create its own row, under its own cap.
polaris_noise_filter("polaris.logs", 0, rec("PUT", "/api/management/v1/catalogs/c1/catalog-roles/nobody/grants", 403, 88))

local _, _, out = polaris_noise_filter("polaris.report", 0, {tick="x", _now_override=T0+90})
local sum, res, sr, sp = nil, {}, 0, 0
for _, r in ipairs(out or {}) do
  local d = r[2] or r
  if d.report_type=="summary" then sum=d
  elseif d.report_type=="resource" then res[d.resource]=d; sr=sr+d.requests
  elseif d.report_type=="principal" then sp=sp+d.requests end
end
assert(sum, "no summary row -- did the window turn over?")

print("== last_* sampling: 2xx only, size > 0, last-wins, absent if none ==")
check("table last_write == the commit",  res[T].last_write_bytes, 5140)
check("table last_read == the LAST get", res[T].last_read_bytes,  5203)
check("config last_write absent",        res["/api/catalog/v1/config"].last_write_bytes, "nil")
check("oauth last_read absent",          res["/api/catalog/v1/oauth/tokens"].last_read_bytes, "nil")

print("== classification: kind only, method still decides read/write ==")
check("oauth/tokens -> auth",        res["/api/catalog/v1/oauth/tokens"].resource_kind, "auth")
check("v1/config -> config",         res["/api/catalog/v1/config"].resource_kind, "config")
check("tables/rename -> table",      res[CAT.."/tables/rename"].resource_kind, "table")
check("views/rename -> view",        res[CAT.."/views/rename"].resource_kind, "view")
check("ns/properties -> namespace",  res[CAT.."/namespaces/ns1/properties"].resource_kind, "namespace")
check("transactions/commit -> transaction",
      res[CAT.."/transactions/commit"] and res[CAT.."/transactions/commit"].resource_kind, "transaction")
check("  key is the whole path, unchanged",
      res[CAT.."/transactions/commit"] ~= nil, true)
check("  POST commit is a WRITE",    res[CAT.."/transactions/commit"].writes, 1)
check("  api_kind catalog",          res[CAT.."/transactions/commit"].api_kind, "catalog")
check("  NOT folded into a table row", res[CAT.."/transactions"], "nil")
check("POST properties is a WRITE",  res[CAT.."/namespaces/ns1/properties"].writes, 1)
check("POST properties is not a read", res[CAT.."/namespaces/ns1/properties"].reads, 0)

print("== roles: grants fold into the role they are granted on ==")
local CRrow = res[CR]
check("catalog-role row exists",        CRrow ~= nil, true)
check("  kind",                         CRrow and CRrow.resource_kind, "catalog-role")
check("  3 grants + 1 read = 4 req",    CRrow and CRrow.requests, 4)
check("  writes == the grant count",    CRrow and CRrow.writes, 3)
check("  reads == the CRUD read",       CRrow and CRrow.reads, 1)
check("  last_write == last grant",     CRrow and CRrow.last_write_bytes, 21)
check("no separate /grants row",        res[CR.."/grants"], "nil")
check("other catalog role is its own row",
      res["/api/management/v1/catalogs/c1/catalog-roles/reader"] ~= nil, true)
check("assignment keys to the PRINCIPAL role",
      res["/api/management/v1/principal-roles/pr1"] and
      res["/api/management/v1/principal-roles/pr1"].requests, 2)
check("  and its kind",                 res["/api/management/v1/principal-roles/pr1"] and
      res["/api/management/v1/principal-roles/pr1"].resource_kind, "principal-role")
check("no __authorization__ row",       res["__authorization__"], "nil")
check("principal-roles collection",     res["/api/management/v1/principal-roles"] and
      res["/api/management/v1/principal-roles"].resource_kind, "collection")
check("principal's role list is its own key",
      res["/api/management/v1/principals/p1/principal-roles"] ~= nil, true)
print("== api_kind: the API SURFACE, orthogonal to resource_kind ==")
local P1 = res["/api/management/v1/principals/p1"]
check("principal kind (was 'management')", P1 and P1.resource_kind, "principal")
check("  api_kind",                        P1 and P1.api_kind, "management")
check("catalog-role api_kind",             CRrow and CRrow.api_kind, "management")
check("catalog-role kind unchanged",       CRrow and CRrow.resource_kind, "catalog-role")
check("table api_kind",                    res[T] and res[T].api_kind, "catalog")
check("table kind unchanged",              res[T] and res[T].resource_kind, "table")
check("no resource_kind == 'management' anywhere", (function()
        for _,d in pairs(res) do if d.resource_kind == "management" then return "found" end end
        return "none" end)(), "none")
check("denied grant keeps its role row",
      res["/api/management/v1/catalogs/c1/catalog-roles/nobody"] ~= nil, true)
check("  and records the denial",
      res["/api/management/v1/catalogs/c1/catalog-roles/nobody"] and
      res["/api/management/v1/catalogs/c1/catalog-roles/nobody"].auth_denied, 1)
check("  did NOT fall to the error bucket", res["__errors__"], "nil")
check("role_keys_forced counts it", sum.role_keys_forced, 1)
-- a 404 on an unknown TABLE: not a role kind, so its attribution is lost -- but it
-- must land in __errors__ (kind "error"), never in __other__, which is cap overflow.
polaris_noise_filter("polaris.logs", 0, rec("GET", CAT.."/namespaces/ns1/tables/ghost", 404, 51))
-- A HYPOTHETICAL FUTURE API, unmatched by every rule. It must get its OWN row with the
-- real path and the correct api_kind -- NOT __other__ -- so that whoever adds the next
-- endpoint can see exactly what needs classifying. This is the future-proofing property,
-- pinned by a test so a later refactor cannot quietly route unknowns into a bucket.
polaris_noise_filter("polaris.logs", 0, rec("POST", "/api/management/v1/quotas/q1", 200, 12))
polaris_noise_filter("polaris.logs", 0, rec("GET",  "/api/catalog/v1/cat1/statistics", 200, 34))
local _,_,out2 = polaris_noise_filter("polaris.report", 0, {tick="x", _now_override=T0+150})
local res2 = {}
for _, r in ipairs(out2 or {}) do local d=r[2] or r
  if d.report_type=="resource" then res2[d.resource]=d end end
print("== __other__ split into overflow vs lost attribution ==")
check("unknown-resource 404 -> __errors__", res2["__errors__"] and res2["__errors__"].requests, 1)
check("  kind is 'error'",                  res2["__errors__"] and res2["__errors__"].resource_kind, "error")
check("  api_kind mixed",                   res2["__errors__"] and res2["__errors__"].api_kind, "mixed")
check("  NOT in __other__ (cap overflow)",  res2["__other__"], "nil")
print("== a future API gets its own row, not a bucket ==")
check("unknown mgmt path keeps its path",
      res2["/api/management/v1/quotas/q1"] ~= nil, true)
check("  resource_kind",  res2["/api/management/v1/quotas/q1"] and
      res2["/api/management/v1/quotas/q1"].resource_kind, "other")
check("  api_kind still correct", res2["/api/management/v1/quotas/q1"] and
      res2["/api/management/v1/quotas/q1"].api_kind, "management")
check("unknown catalog path keeps its path",
      res2["/api/catalog/v1/cat1/statistics"] ~= nil, true)
check("  api_kind still correct", res2["/api/catalog/v1/cat1/statistics"] and
      res2["/api/catalog/v1/cat1/statistics"].api_kind, "catalog")
-- min/max_record_time: PRESENT with traffic, ABSENT (not "") on an idle window. The `or ""`
-- this replaced was a mapping fault, not a cosmetic one: OpenSearch dynamic-maps the field
-- from the first document and keeps it for the life of the index, and at 30s windows a fresh
-- daily index almost always opens idle. Measured text-mapped in polaris-report-2026.09.10.
print("== min/max_record_time: absent on an idle window, never an empty string ==")
check("traffic window HAS min_record_time", sum.min_record_time, "2026-09-09T08:00:05.000Z")
check("traffic window HAS max_record_time", sum.max_record_time, "2026-09-09T08:00:05.000Z")
local _,_,out3 = polaris_noise_filter("polaris.report", 0, {tick="x", _now_override=T0+210})
local sum3
for _, r in ipairs(out3 or {}) do local d=r[2] or r
  if d.report_type=="summary" then sum3=d end end
check("idle window emitted a summary",   sum3 ~= nil, true)
check("  access_seen 0",                 sum3 and sum3.access_seen, 0)
check("  min_record_time ABSENT",        sum3 and sum3.min_record_time, "nil")
check("  max_record_time ABSENT",        sum3 and sum3.max_record_time, "nil")

check("sum(resource) == seen-parse", sr, sum.access_seen - sum.parse_errors)
check("sum(principal) == seen-parse", sp, sum.access_seen - sum.parse_errors)
-- 2026-09-15: the deployed script is v4. Every v3 behaviour above still holds; only the
-- version constant moved. v4-only behaviour is in test-schema-v4.lua.
check("schema_version", sum.schema_version, 5)

print()
if fails == 0 then print("ALL PASS") else print(fails .. " FAILURE(S)") ; os.exit(1) end
