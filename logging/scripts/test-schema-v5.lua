-- 리포트 스키마 v5 / 정책 v5 회귀 테스트 — 404 집계만 + 요청 ID 보류.
--
--   cp fluent-bit/polaris_access_log.lua /tmp/polaris.lua
--   luajit logging/scripts/test-schema-v5.lua
--
-- v3/v4 동작은 test-schema-v3.lua / test-schema-v4.lua 가 계속 검증한다 (schema_version 기대값 5).
-- WINDOW_SECONDS 30 을 가정한다 (틱 _now_override 로 30초씩 넘긴다).
dofile("/tmp/polaris.lua")
dofile("logging/scripts/test-raw-access-shim.lua")   -- 액세스 라인을 _msg 원문으로 넣는다 (분리형·병합형 공통)
local T0 = 1788940800
local A  = "io.quarkus.http.access-log"
local MAPPER = "org.apache.polaris.service.exception.IcebergExceptionMapper"
local ADMIN  = "org.apache.polaris.service.admin.PolarisServiceImpl"
local fails = 0
local function check(name, got, want)
  local ok = tostring(got) == tostring(want)
  if not ok then fails = fails + 1 end
  print(string.format("  [%s] %-58s got=%-10s want=%s", ok and "PASS" or "FAIL", name, tostring(got), tostring(want)))
end
local NOW = T0 + 5
local function acc(rid, m, p, st, sz)
  return { loggerName=A, level="INFO", http_method=m, api_path=p, http_status=tostring(st),
           response_size=tostring(sz or 10), user_principal_name="svc", mdc={ requestId=rid },
           _time="2026-09-16T00:00:05.000Z", _now_override=NOW }
end
local function app(rid, logger, msg, level)
  return { loggerName=logger, level=level or "INFO", _msg=msg, mdc=rid and { requestId=rid } or nil,
           _time="2026-09-16T00:00:05.000Z", _now_override=NOW }
end
-- returns: code, list of records emitted (possibly empty)
local function feed(r)
  local code, _, out = polaris_noise_filter("polaris.logs", 0, r)
  if code == -1 then return code, {} end
  if type(out) == "table" and out[1] ~= nil and type(out[1]) == "table" then return code, out end
  return code, { out }
end
local function tick(t)
  local _, _, out = polaris_noise_filter("polaris.report", 0, { _now_override = t })
  local rep = { resource = {}, principal = {} }
  if type(out) == "table" and out[1] ~= nil then
    for _, d in ipairs(out) do
      if d.report_type == "summary" then rep.summary = d
      elseif d.report_type == "resource" then rep.resource[d.resource] = d
      elseif d.report_type == "principal" then rep.principal[d.user_principal_name] = d end
    end
  end
  return rep
end
local CAT = "/api/catalog/v1/cat1"
tick(T0 + 1)

print("== 404: 액세스 라인과 같은 요청의 앱 로그를 함께 버린다 ==")
local c, o = feed(app("r404", MAPPER, "Handling runtimeException Table does not exist: ns.t"))
check("예외 로그는 보류 (-1)", c, -1)
c, o = feed(app("r404", ADMIN, "Assigning catalogRole x in catalog c to principalRole y"))
check("같은 ID 의 grant 로그도 보류", c, -1)
c, o = feed(acc("r404", "GET", CAT .. "/namespaces/ns/tables/t", 404, 51))
check("404 액세스 라인: 적재 안 함", c, -1)
check("  아무것도 내보내지 않음", #o, 0)

print("== 403: 보류분이 액세스 라인과 함께 나간다 (앞에) ==")
feed(app("r403", MAPPER, "Handling runtimeException Principal 'p' is not authorized"))
c, o = feed(acc("r403", "GET", CAT .. "/namespaces/ns/tables/t", 403, 88))
check("레코드 배열로 반환 (code 2)", c, 2)
check("  2건", #o, 2)
check("  보류분이 먼저", o[1] and o[1].loggerName, MAPPER)
check("  액세스 라인이 뒤", o[2] and o[2].loggerName, A)

print("== 200 PUT: grant 로그 + 액세스 라인 ==")
feed(app("rput", ADMIN, "Adding grant class AddGrantRequest {"))
c, o = feed(acc("rput", "PUT", "/api/management/v1/catalogs/c1/catalog-roles/cr/grants", 201, 19))
check("2건 적재", #o, 2)

print("== 2xx GET(집계만) 에 보류분이 있으면 보류분만 나간다 ==")
feed(app("rget", MAPPER, "Handling runtimeException odd but kept"))
c, o = feed(acc("rget", "GET", CAT .. "/namespaces/ns/tables/t", 200, 500))
check("액세스는 버리고 보류분 1건만", #o, 1)
check("  그 1건은 앱 로그", o[1] and o[1].loggerName, MAPPER)

print("== 액세스 라인 뒤에 온 앱 로그: 기억한 상태로 즉시 판정 ==")
c, o = feed(app("r404", MAPPER, "late line of the 404 request"))
check("404 요청의 늦은 로그는 버림", c, -1)
c, o = feed(app("rput", ADMIN, "late grant line of a 201 request"))
check("201 요청의 늦은 로그는 즉시 적재", #o, 1)

print("== 요청 ID 없음 / ERROR ==")
c, o = feed(app(nil, MAPPER, "no request id"))
check("요청 ID 없으면 즉시 적재 (v4 동작)", #o, 1)
c, o = feed(app("r404b", MAPPER, "Unhandled exception", "ERROR"))
check("ERROR 는 요청 ID 가 있어도 즉시 적재", #o, 1)
feed(acc("r404b", "DELETE", CAT .. "/namespaces/ns/tables/gone", 404, 0))

print("== 고아: 짝 없는 보류분은 HOLD_MAX_SECONDS 뒤 다음 레코드와 함께 ==")
feed(app("rorphan", MAPPER, "access line never comes"))
NOW = T0 + 5 + 31
c, o = feed(acc("rlater", "GET", CAT .. "/namespaces/ns/tables/t", 200, 10))
check("고아 1건이 함께 나감", #o, 1)
check("  held_orphan 표시", o[1] and o[1].held_orphan, true)
NOW = T0 + 5

print("== 윈도우 요약 ==")
local r = tick(T0 + 31 + 30)
local s = r.summary
check("schema_version 5", s.schema_version, 5)
check("counted_404 (r404, r404b)", s.counted_404, 2)
check("app_dropped_404 (2 보류 + 1 늦음)", s.app_dropped_404, 3)
check("held_orphans", s.held_orphans, 1)
check("held_pending 0", s.held_pending, 0)
check("errors_kept 은 404 제외 (403 만)", s.errors_kept, 1)
check("errors_4xx 는 404 포함 (404×2 + 403)", s.errors_4xx, 3)
check("access_seen - access_counted == access_kept", s.access_seen - s.access_counted, s.access_kept)
local sr, sp = 0, 0
for _, d in pairs(r.resource) do sr = sr + d.requests end
for _, d in pairs(r.principal) do sp = sp + d.requests end
check("sum(resource) == seen - parse_errors", sr, s.access_seen - s.parse_errors)
check("sum(principal) == seen - parse_errors", sp, s.access_seen - s.parse_errors)
check("404 는 principal 행 errors_4xx 에 반영", r.principal["svc"] and r.principal["svc"].errors_4xx, 3)

print("== register 분류 ==")
feed(acc("rreg", "POST", CAT .. "/namespaces/ns/register", 200, 900))
local r2 = tick(T0 + 121)
local reg = r2.resource[CAT .. "/namespaces/ns/register"]
check("register 행", reg ~= nil, true)
check("  kind collection", reg and reg.resource_kind, "collection")

print()
if fails == 0 then print("ALL PASS") else print(fails .. " FAILURE(S)"); os.exit(1) end
