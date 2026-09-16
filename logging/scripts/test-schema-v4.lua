-- 리포트 스키마 v4 / 정책 v4 회귀 테스트. "배포되는" 스크립트 텍스트에 대해 돌린다.
--
--   cp fluent-bit/polaris_access_log.lua /tmp/polaris.lua     # 배포되는 스크립트 파일 그대로
--   luajit logging/scripts/test-schema-v4.lua        # Fluent Bit 과 같은 LuaJIT (lua5.1 도 가능)
--   luajit logging/scripts/test-schema-v3.lua        # v3 동작(분류, last_*, 롤, __errors__)
--
-- 틱 시각을 _now_override 로 30초씩 넘겨 윈도우를 닫으므로 WINDOW_SECONDS 가 30 이어야 한다.
-- 운영값 1800 으로 되돌린 뒤에는 추출 결과에 sed 's/^local WINDOW_SECONDS = 1800/local WINDOW_SECONDS = 30/' 를 적용할 것.
dofile("/tmp/polaris.lua")
local T0 = 1788940800                 -- 30초 경계에 정렬된 시각
local A  = "io.quarkus.http.access-log"
local fails = 0
local function check(name, got, want)
  local ok = tostring(got) == tostring(want)
  if not ok then fails = fails + 1 end
  print(string.format("  [%s] %-52s got=%-10s want=%s", ok and "PASS" or "FAIL", name,
                      tostring(got), tostring(want)))
end
local function acc(m, p, st, sz, user)
  return { loggerName=A, level="INFO", http_method=m, api_path=p, http_status=tostring(st),
           response_size=tostring(sz), user_principal_name=user or "svc",
           _time="2026-09-15T08:00:05.000Z" }
end
local function app(logger, msg, level)
  return { loggerName=logger, level=level or "INFO", _msg=msg, _time="2026-09-15T08:00:05.000Z" }
end
local function feed(r) local code = polaris_noise_filter("polaris.logs", 0, r); return code end
local function tick(t)
  local _, _, out = polaris_noise_filter("polaris.report", 0, {tick="x", _now_override=t})
  local rep = { summary=nil, resource={}, principal={}, app_dropped={}, n=0 }
  if type(out) == "table" and out[1] ~= nil then
    for _, d in ipairs(out) do
      rep.n = rep.n + 1
      if d.report_type == "summary" then rep.summary = d
      elseif d.report_type == "resource" then rep.resource[d.resource] = d
      elseif d.report_type == "principal" then rep.principal[d.user_principal_name] = d
      elseif d.report_type == "app_dropped" then rep.app_dropped[d.logger_name] = d end
    end
  end
  return rep
end

local MAPPER = "org.apache.polaris.service.exception.IcebergExceptionMapper"
local ADMIN  = "org.apache.polaris.service.admin.PolarisServiceImpl"
local HANDLER= "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler"
local ICAT   = "org.apache.polaris.service.catalog.iceberg.IcebergCatalog"
local CAT    = "/api/catalog/v1/cat1"

tick(T0 + 1)                          -- 첫 틱: 윈도우만 연다

print("== 규칙 2: 허용 목록 ==")
check("IcebergExceptionMapper INFO 적재",  feed(app(MAPPER, "Handling runtimeException Table does not exist: ns.t")), 0)
check("PolarisServiceImpl INFO 적재",      feed(app(ADMIN,  "Adding grant class AddGrantRequest {")), 0)
check("IcebergCatalogHandler INFO 버림",   feed(app(HANDLER,"Initializing non-federated catalog")), -1)
check("  두 번째도 버림",                   feed(app(HANDLER,"Initializing non-federated catalog")), -1)
check("모르는 logger INFO 버림",           feed(app("org.example.New", "hello")), -1)
check("모르는 logger WARN 은 적재",         feed(app("org.example.New", "careful", "WARN")), 0)
check("모르는 logger ERROR 는 적재",        feed(app("org.example.New", "boom", "ERROR")), 0)
check("loggerName 없는 레코드 버림",        feed({ level="INFO", _msg="x" }), -1)

print("== 자격증명 가드 ==")
local masked = app(ADMIN, "Created new principal\n    credentials: class X {\n        clientSecret: *\n    }")
check("마스킹된 시크릿: 적재, 변경 없음(0)", feed(masked), 0)
check("  secret_redacted 없음",            masked.secret_redacted, "nil")
local leaked = app(ADMIN, "Created new principal\n        clientId: abc\n        clientSecret: s3cr3tValue\n")
check("평문 시크릿: 적재, 변경됨(2)",       feed(leaked), 2)
check("  값이 치환됨",                      leaked._msg:find("s3cr3tValue", 1, true) == nil, true)
check("  <redacted> 로",                    leaked._msg:find("clientSecret: <redacted>", 1, true) ~= nil, true)
check("  secret_redacted=true",            leaked.secret_redacted, true)

print("== 2a: 커밋 시간 수확 ==")
local T  = CAT .. "/namespaces/ns1/tables/orders"
local V  = CAT .. "/namespaces/ns1/views/v1"
local T2 = CAT .. "/namespaces/a%1Fb/tables/deep"
local TX = CAT .. "/namespaces/ns1/tables/tx_only"
feed(acc("POST", T, 200, 1941))                                   -- 커밋 요청 (집계만)
check("커밋 라인 자체는 버림", feed(app(ICAT, "Successfully committed to table cat1.ns1.orders in 20 ms")), -1)
feed(app(ICAT, "Successfully committed to table cat1.ns1.orders in 57 ms"))
feed(app(ICAT, "Successfully committed to table cat1.ns1.orders in 10 ms"))
feed(app(ICAT, "Refreshing table cat1.ns1.orders from new version: s3://b/x"))   -- 수확 안 함
feed(acc("POST", V, 200, 900))
feed(app(ICAT, "Successfully committed to view cat1.ns1.v1 in 32 ms"))
feed(acc("GET", T2, 200, 700))                                    -- 2단계 네임스페이스 요청
feed(app(ICAT, "Successfully committed to table cat1.a.b.deep in 14 ms"))
feed(app(ICAT, "Successfully committed to table cat1.ns1.tx_only in 40 ms"))   -- 트랜잭션으로만 변경
feed(acc("POST", CAT .. "/transactions/commit", 204, 0))
feed(app(ICAT, "Successfully committed to table bad in 5 ms"))    -- 조각 < 3: 무시

local r1 = tick(T0 + 31)
local R  = r1.resource
check("table 행 commit_count",     R[T] and R[T].commit_count, 3)
check("  commit_ms_sum",           R[T] and R[T].commit_ms_sum, 87)
check("  commit_ms_min",           R[T] and R[T].commit_ms_min, 10)
check("  commit_ms_max",           R[T] and R[T].commit_ms_max, 57)
check("  requests 는 액세스만",     R[T] and R[T].requests, 1)
check("  avg 필드는 저장 안 함",     R[T] and R[T].commit_ms_avg, "nil")
check("  _msg 에 min/avg/max",      R[T] and R[T]._msg:find("commits 3 (min/avg/max 10/29/57 ms)", 1, true) ~= nil, true)
check("view 행에 커밋",            R[V] and R[V].commit_count, 1)
check("  resource_kind view",      R[V] and R[V].resource_kind, "view")
check("a.b → a%1Fb, 요청 행과 같은 키", R[T2] and R[T2].commit_count, 1)
check("  그 행의 requests",         R[T2] and R[T2].requests, 1)
check("  유령 행 a.b 없음",          R[CAT .. "/namespaces/a.b/tables/deep"], "nil")
check("트랜잭션만: requests 0 행도 냄", R[TX] and R[TX].requests, 0)
check("  commit_count",            R[TX] and R[TX].commit_count, 1)
check("  api_kind catalog",        R[TX] and R[TX].api_kind, "catalog")
check("커밋 없는 행엔 commit_* 부재", R[CAT .. "/transactions/commit"] and R[CAT .. "/transactions/commit"].commit_count, "nil")

print("== 2c: app_dropped ==")
local D = r1.app_dropped
check("IcebergCatalogHandler 2줄",  D[HANDLER] and D[HANDLER].dropped, 2)
check("org.example.New INFO 1줄",   D["org.example.New"] and D["org.example.New"].dropped, 1)
check("loggerName 없음 → '-'",       D["-"] and D["-"].dropped, 1)
check("IcebergCatalog 8줄 (커밋 7 + Refreshing 1)", D[ICAT] and D[ICAT].dropped, 8)
check("허용 logger 는 app_dropped 에 없음", D[ADMIN], "nil")
check("summary.app_dropped_total",  r1.summary.app_dropped_total, 12)
check("schema_version 5 (v5 파일에서도 v4 동작 유지)", r1.summary.schema_version, 5)
check("carried_rows 필드 없음",       r1.summary.carried_rows, "nil")

print("== 불변식 ==")
local sr, sp = 0, 0
for _, d in pairs(R) do sr = sr + d.requests end
for _, d in pairs(r1.principal) do sp = sp + d.requests end
local seen = r1.summary.access_seen - r1.summary.parse_errors
check("sum(resource.requests) == seen - parse_errors",  sr, seen)
check("sum(principal.requests) == seen - parse_errors", sp, seen)
check("distinct_resources 는 요청>0 만 (tx_only 제외)", r1.summary.distinct_resources, 4)

print("== D3: zero-carry 없음 ==")
feed(acc("GET", CAT .. "/namespaces/ns1/tables/other", 200, 10))
local r2 = tick(T0 + 61)
check("직전 윈도우 키는 0 행으로 안 나옴", r2.resource[T], "nil")
check("이번 요청 주체의 principal 행",      r2.principal["svc"] ~= nil, true)
check("이번 윈도우 행만",                 r2.n, 3)   -- summary + resource 1 + principal 1
check("app_dropped 는 0 이면 없음",        next(r2.app_dropped), "nil")
local r3 = tick(T0 + 91)
check("유휴 윈도우: summary 1건만",        r3.n, 1)
check("  access_seen 0",                  r3.summary and r3.summary.access_seen, 0)
check("  min_record_time 부재",           r3.summary and r3.summary.min_record_time, "nil")

print()
if fails == 0 then print("ALL PASS") else print(fails .. " FAILURE(S)"); os.exit(1) end
