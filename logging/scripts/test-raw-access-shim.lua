-- 테스트 입력 어댑터: test-schema-v3/v4/v5 는 액세스 라인을 "이미 파싱된 필드" 로 만든다
-- (http_method, api_path, http_status, response_size, user_principal_name). 운영 입력은 _msg 원문뿐이다.
-- 이 shim 은 그 필드로 Quarkus 액세스 라인(_msg)을 만들고 파싱된 필드를 지운 뒤, 스크립트에
-- polaris_access_log(구 FILTER 2)가 있으면 먼저 통과시킨다. 그래서 같은 테스트가
--   * 분리형 (FILTER 2 polaris_access_log + FILTER 3 polaris_noise_filter) 과
--   * 병합형 (2026-09-16 리팩터 R1, polaris_noise_filter 가 직접 파싱)
-- 양쪽에서 "실제 파싱 경로" 를 거쳐 돈다. dofile(script) 직후에 dofile 할 것.
local A = "io.quarkus.http.access-log"
local inner = polaris_noise_filter
local split = polaris_access_log
polaris_noise_filter = function(tag, ts, r)
    if tag ~= "polaris.report" and type(r) == "table" and r.loggerName == A and r._msg == nil
       and r.http_method ~= nil then
        r._msg = string.format('10.0.0.1 - %s [16/Sep/2026:00:00:05 +0000] "%s %s HTTP/1.1" %s %s',
            tostring(r.user_principal_name or "-"), r.http_method, tostring(r.api_path),
            tostring(r.http_status), tostring(r.response_size))
        r.http_method, r.api_path, r.http_status, r.response_size, r.user_principal_name = nil, nil, nil, nil, nil
    end
    if tag ~= "polaris.report" and split ~= nil then
        local _, _, r2 = split(tag, ts, r)
        r = r2 or r
    end
    return inner(tag, ts, r)
end
