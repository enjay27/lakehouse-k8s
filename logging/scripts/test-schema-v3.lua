-- Regression test for report schema v3, run against the ACTUAL deployed Lua.
--
--   python3 -c "import yaml;print(yaml.safe_load(open('fluent-bit/values.yaml'))['luaScripts']['polaris_access_log.lua'])" > /tmp/polaris.lua
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
polaris_noise_filter("polaris.logs", 0, rec("POST", "/api/catalog/v1/oauth/tokens", 200, 685))
polaris_noise_filter("polaris.logs", 0, rec("GET",  "/api/catalog/v1/config", 200, 1757))
polaris_noise_filter("polaris.logs", 0, rec("PUT",  "/api/management/v1/principal-roles/r1", 200, 77))
polaris_noise_filter("polaris.logs", 0, rec("GET",  "/api/management/v1/principal-roles/r1", 200, 55))

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
check("POST properties is a WRITE",  res[CAT.."/namespaces/ns1/properties"].writes, 1)
check("POST properties is not a read", res[CAT.."/namespaces/ns1/properties"].reads, 0)

print("== exclusion and the margin invariant ==")
check("principal-roles row suppressed", res["/api/management/v1/principal-roles/r1"], "nil")
check("excluded_requests", sum.excluded_requests, 2)
check("sum(resource)+excluded == seen-parse", sr + sum.excluded_requests,
      sum.access_seen - sum.parse_errors)
check("sum(principal) == seen-parse", sp, sum.access_seen - sum.parse_errors)
check("schema_version", sum.schema_version, 3)

print()
if fails == 0 then print("ALL PASS") else print(fails .. " FAILURE(S)") ; os.exit(1) end
