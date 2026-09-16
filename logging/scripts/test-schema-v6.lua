-- 리포트 스키마 v6 회귀 테스트 — 메시지 필드 이름 `message`, 리포트 봉투 app/level 제거, 문장은 요약 행에만.
--
--   cp fluent-bit/polaris_access_log.lua /tmp/polaris.lua && luajit logging/scripts/test-schema-v6.lua
-- 정책 동작(적재/집계)은 v3/v4/v5 테스트가 본다. 여기서는 v6 에서 바뀐 "문서 모양" 만 본다.
dofile("/tmp/polaris.lua")
dofile("logging/scripts/test-raw-access-shim.lua")
local T0 = 1788940800
local A = "io.quarkus.http.access-log"
local ADMIN = "org.apache.polaris.service.admin.PolarisServiceImpl"
local HANDLER = "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler"
local fails = 0
local function check(name, got, want)
  local ok = tostring(got) == tostring(want)
  if not ok then fails = fails + 1 end
  print(string.format("  [%s] %-52s got=%-10s want=%s", ok and "PASS" or "FAIL", name, tostring(got), tostring(want)))
end
local function feed(r)
  local code, _, out = polaris_noise_filter("polaris.logs", 0, r)
  if code == -1 then return code, nil end
  if type(out) == "table" and type(out[1]) == "table" then return code, out[#out] end
  return code, out
end
polaris_noise_filter("polaris.report", 0, { tick="x", _now_override=T0 + 1 })

print("== 입력·저장 필드 이름: message ==")
local c, o = feed({ loggerName=A, level="INFO", http_method="PUT", api_path="/api/management/v1/principals/p",
                    http_status="200", response_size="12", user_principal_name="svc", _time="2026-09-16T00:00:05.000Z", _now_override=T0 + 5 })
check("PUT 액세스 라인 적재", c, 2)
check("  파싱됨 (http_status)", o and o.http_status, 200)
check("  원문은 message 에", o and type(o.message), "string")
check("  _msg 없음", o and o._msg, "nil")
local leaked = { loggerName=ADMIN, level="INFO", message="Created new principal\n  clientSecret: s3cr3t\n", _time="2026-09-16T00:00:05.000Z", _now_override=T0 + 5 }
c, o = feed(leaked)
check("시크릿 가드는 message 를 본다", leaked.message:find("s3cr3t", 1, true), "nil")
check("  secret_redacted", leaked.secret_redacted, true)
check("_msg 만 가진 액세스 라인 = 파싱 실패 (입력 계약 변경)", (function()
  local r = { loggerName=A, level="INFO", _msg='1.2.3.4 - u [x] "GET /a HTTP/1.1" 200 1', _time="2026-09-16T00:00:05.000Z", _now_override=T0 + 5 }
  polaris_noise_filter("polaris.logs", 0, r); return r.access_log_parse_error end)(), true)
feed({ loggerName=HANDLER, level="INFO", message="Initializing non-federated catalog", _time="2026-09-16T00:00:05.000Z", _now_override=T0 + 5 })

print("== 리포트 문서 모양 ==")
local _, _, out = polaris_noise_filter("polaris.report", 0, { tick="x", _now_override=T0 + 31 })
local kinds, rows_with_msg, with_app, with_level, summary = {}, 0, 0, 0, nil
for _, d in ipairs(out) do
  kinds[d.report_type] = (kinds[d.report_type] or 0) + 1
  if d.app ~= nil then with_app = with_app + 1 end
  if d.level ~= nil then with_level = with_level + 1 end
  if d._msg ~= nil then rows_with_msg = rows_with_msg + 1 end
  if d.report_type == "summary" then summary = d elseif d.message ~= nil then rows_with_msg = rows_with_msg + 1 end
end
check("summary 1행", kinds.summary, 1)
check("resource / principal / app_dropped 행 있음", (kinds.resource or 0) > 0 and (kinds.principal or 0) > 0 and (kinds.app_dropped or 0) > 0, true)
check("schema_version 6", summary.schema_version, 6)
check("summary 에 message 문장", type(summary.message), "string")
check("summary 에 _msg 없음", summary._msg, "nil")
check("행에 문장 없음 (_msg / message)", rows_with_msg, 0)
check("app 필드 없음 (전 문서)", with_app, 0)
check("level 필드 없음 (전 문서)", with_level, 0)
check("봉투 필드는 유지: window_start", summary.window_start ~= nil, true)
check("봉투 필드는 유지: hostname / report_seq", summary.hostname ~= nil and summary.report_seq ~= nil, true)

print()
if fails == 0 then print("ALL PASS") else print(fails .. " FAILURE(S)"); os.exit(1) end
