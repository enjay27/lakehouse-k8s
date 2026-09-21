-- R4 (2026-09-16 리팩터): 기동 직후 첫 틱 "이전" 에 들어온 레코드도 집계되는가.
--   cp fluent-bit/polaris_access_log.lua /tmp/polaris.lua && luajit logging/scripts/test-first-tick.lua
-- 리팩터 이전 스크립트는 6건 FAIL 한다 (첫 틱 전 레코드가 어느 카운터에도 없었다). apply-lua.sh 가 돌린다.
dofile("/tmp/polaris.lua")
dofile("logging/scripts/test-raw-access-shim.lua")
local T0 = 1788940800
local A = "io.quarkus.http.access-log"
local MAPPER = "org.apache.polaris.service.exception.IcebergExceptionMapper"
local fails = 0
local function check(name, got, want)
  local ok = tostring(got) == tostring(want)
  if not ok then fails = fails + 1 end
  print(string.format("  [%s] %-50s got=%-8s want=%s", ok and "PASS" or "FAIL", name, tostring(got), tostring(want)))
end
local function acc(rid, m, p, st, t)
  return { loggerName=A, level="INFO", http_method=m, api_path=p, http_status=tostring(st), response_size="10",
           user_principal_name="svc", mdc={ requestId=rid }, _time="2026-09-16T00:00:02.000Z", _now_override=t }
end
local CAT = "/api/catalog/v1/cat1"
-- 파드 기동: 틱보다 레코드가 먼저 온다 (Interval_Sec 5 → 최대 5초)
polaris_noise_filter("polaris.logs", 0, acc("a", "GET", CAT .. "/namespaces/ns/tables/t", 200, T0 + 2))
polaris_noise_filter("polaris.logs", 0, acc("b", "POST", CAT .. "/namespaces/ns/tables/t", 200, T0 + 2))
polaris_noise_filter("polaris.logs", 0, { loggerName=MAPPER, level="INFO", message="Handling runtimeException x",
                                          mdc={ requestId="c" }, _time="2026-09-16T00:00:02.000Z", _now_override=T0 + 3 })
polaris_noise_filter("polaris.logs", 0, acc("c", "GET", CAT .. "/namespaces/ns/tables/gone", 404, T0 + 3))
polaris_noise_filter("polaris.logs", 0, { loggerName="org.x.Noise", level="INFO", message="n", _time="2026-09-16T00:00:03.000Z", _now_override=T0 + 3 })
-- 첫 틱 (같은 윈도우), 그리고 경계를 넘은 틱
polaris_noise_filter("polaris.report", 0, { tick="x", _now_override=T0 + 4 })
local code, _, out = polaris_noise_filter("polaris.report", 0, { tick="x", _now_override=T0 + 31 })
local s = (code == 2 and type(out) == "table") and out[1] or {}
check("경계에서 리포트가 나온다", code, 2)
check("access_seen (첫 틱 이전 3건)", s.access_seen, 3)
check("counted_read", s.counted_read, 1)
check("counted_post", s.counted_post, 1)
check("counted_404", s.counted_404, 1)
check("app_dropped_404", s.app_dropped_404, 1)
check("app_dropped_total", s.app_dropped_total, 1)
check("partial_window true (기동 윈도우)", s.partial_window, "true")
check("window_start = 레코드 시각의 윈도우", s.window_start, os.date("!%Y-%m-%dT%H:%M:%SZ", T0))
print()
if fails == 0 then print("ALL PASS") else print(fails .. " FAILURE(S)"); os.exit(1) end
