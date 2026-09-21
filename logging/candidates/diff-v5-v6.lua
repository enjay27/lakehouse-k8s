-- 차등 검사 (v5 → v6): 병합형 v5 스크립트(입력 _msg)와 v6(입력 message)에 같은 로그를 넣고, v6 의 의도된 차이
-- (필드 이름 message, 리포트의 app/level/문장/schema_version)만 정규화한 뒤 나머지 전부를 비교한다.
-- 반환 코드·내보낸 레코드 전체(모든 필드)·리포트 행 전체를 비교한다.
--   luajit logging/candidates/diff-refactor.lua fluent-bit/polaris_access_log.lua \
--          logging/candidates/polaris_access_log.refactor.lua /tmp/tier1_all.lua [fuzz_n]
-- 입력 1: 실데이터 (step10 readout 의 tier1.json, 레코드 시각을 _now_override 로) — 5초마다 틱.
-- 입력 2: 합성 퍼즈 — 요청 ID 재사용, 404/403/5xx, WARN 액세스, 파싱 실패, 시크릿, 커밋,
--         고아 만료, 상한 초과(리소스/principal/logger), 잠자기(windows_skipped).
-- 첫 틱을 레코드보다 먼저 넣는다: R4(첫 틱 이전 집계)는 의도된 차이라 test-r4-first-tick.lua 가 따로 본다.
local function load(path)
    local src = assert(io.open(path)):read("*a")
    local f = assert(loadstring(src, "@" .. path))
    local env = setmetatable({}, { __index = _G })
    setfenv(f, env); f()
    return env
end
local OLD, NEW = load(arg[1]), load(arg[2])

local function ser(v)
    local t = type(v)
    if t == "table" then
        local ks = {}
        for k in pairs(v) do ks[#ks + 1] = k end
        table.sort(ks, function(a, b) return tostring(a) < tostring(b) end)
        local p = {}
        for _, k in ipairs(ks) do p[#p + 1] = tostring(k) .. "=" .. ser(v[k]) end
        return "{" .. table.concat(p, ",") .. "}"
    elseif t == "string" then return string.format("%q", v)
    else return tostring(v) end
end
local function copy(v)
    if type(v) ~= "table" then return v end
    local c = {}
    for k, x in pairs(v) do c[k] = copy(x) end
    return c
end
-- 반환을 "레코드 목록" 으로 정규화. 0 은 입력 그대로 통과 = 입력 레코드 1건.
-- 리포트 행은 pairs 순서가 구현마다 달라도 되므로 정렬한다.
local function norm(code, out, input, is_report)
    if code == -1 then return "DROP" end
    local recs = {}
    if code == 0 then recs = { input }
    elseif type(out) == "table" and type(out[1]) == "table" then recs = out
    else recs = { out } end
    local s = {}
    for i, r in ipairs(recs) do s[i] = ser(v6norm(r, is_report)) end
    if is_report then table.sort(s) end
    return (code == 0 and "PASS" or "MOD") .. "|" .. table.concat(s, "\n")
end
local function old_call(tag, r)
    if tag ~= "polaris.report" and r.message ~= nil then r._msg = r.message; r.message = nil end
    return OLD.polaris_noise_filter(tag, 0, r)
end
local function new_call(tag, r) return NEW.polaris_noise_filter(tag, 0, r) end
function v6norm(d, is_report)
    if type(d) ~= "table" then return d end
    local c = {}
    for k, v in pairs(d) do c[k] = v end
    if is_report then c.app, c.level, c._msg, c.message, c.schema_version = nil, nil, nil, nil, nil
    else if c._msg ~= nil then c.message = c._msg; c._msg = nil end end
    return c
end

local n, bad, emitted, reports = 0, 0, 0, 0
COV = nil
local function step(tag, rec)
    n = n + 1
    local a, b = copy(rec), copy(rec)
    local ca, _, oa = old_call(tag, a)
    local cb, _, ob = new_call(tag, b)
    -- 코드 0(통과, 레코드 불변)과 2(수정)는 내용이 같으면 동등하다: 액세스 라인은 구 FILTER 2 가
    -- 이미 2 를 반환해 수정을 확정했고, 병합형은 한 번에 2 를 반환한다.
    if tag == "polaris.report" and cb == 2 and COV then
        local sm = ob[1]
        for _, f in ipairs({ "resources_other", "principals_other", "held_orphans", "app_dropped_404", "counted_404",
                             "parse_errors", "windows_skipped", "role_keys_forced", "errors_5xx", "held_pending" }) do
            if (tonumber(sm[f]) or 0) > 0 then COV[f] = (COV[f] or 0) + 1 end
        end
        for _, e in ipairs(ob) do
            if e.report_type == "app_dropped" and e.logger_name == "__other__" then COV.dropped_other = (COV.dropped_other or 0) + 1 end
            if e.commit_count then COV.commit_rows = (COV.commit_rows or 0) + 1 end
            if e.resource == "__errors__" then COV.errors_row = (COV.errors_row or 0) + 1 end
        end
    end
    if tag ~= "polaris.report" and cb ~= -1 then
        local list = (type(ob) == "table" and type(ob[1]) == "table") and ob or { ob or b }
        for _, e in ipairs(list) do
            if COV and e.secret_redacted then COV.secret_redacted = (COV.secret_redacted or 0) + 1 end
            if COV and e.held_orphan then COV.held_orphan_docs = (COV.held_orphan_docs or 0) + 1 end
            if COV and e.access_log_parse_error then COV.parse_error_docs = (COV.parse_error_docs or 0) + 1 end
        end
    end
    local na = norm(ca, oa, a, tag == "polaris.report"):gsub("^PASS|", "MOD|")
    local nb = norm(cb, ob, b, tag == "polaris.report"):gsub("^PASS|", "MOD|")
    if na ~= "DROP" then emitted = emitted + 1 end
    if tag == "polaris.report" and ca == 2 then reports = reports + 1 end
    if na ~= nb then
        bad = bad + 1
        if bad <= 5 then
            print("DIFF at input " .. n .. " tag " .. tag .. " " .. ser(rec))
            print("  old: " .. na:sub(1, 900))
            print("  new: " .. nb:sub(1, 900))
        end
    end
end

-- ── 입력 1: 실데이터 ──
local data = dofile(arg[3])
local W = 30
local t0 = data[1].now
local last_tick = math.floor(t0 / W) * W - 1
step("polaris.report", { tick = "x", _now_override = last_tick })
for _, r in ipairs(data) do
    while last_tick + 5 <= r.now do
        last_tick = last_tick + 5
        step("polaris.report", { tick = "x", _now_override = last_tick })
    end
    local rec = { loggerName = r.loggerName, level = r.level, message = r._msg, _time = r._time,
                  mdc = r.mdc, _now_override = r.now }
    step("polaris.logs", rec)
end
step("polaris.report", { tick = "x", _now_override = last_tick + 3600 })
print(string.format("real:  %d calls, %d emitting, %d reports, %d diffs", n, emitted, reports, bad))

-- ── 입력 2: 합성 퍼즈 (두 스크립트의 상태를 새로 연다) ──
OLD, NEW = load(arg[1]), load(arg[2])
COV = {}
local TICK = tonumber(arg[5]) or 8        -- 1000 입력당 틱 수. 작을수록 윈도우가 커져 상한에 닿는다
local N = tonumber(arg[4]) or 200000
math.randomseed(20260916)
local R = math.random
local A = "io.quarkus.http.access-log"
local LOGGERS = { "org.apache.polaris.service.exception.IcebergExceptionMapper",
                  "org.apache.polaris.service.admin.PolarisServiceImpl",
                  "org.apache.polaris.service.catalog.iceberg.IcebergCatalog",
                  "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler" }
local METHODS = { "GET", "GET", "GET", "HEAD", "POST", "POST", "PUT", "DELETE", "PATCH", "OPTIONS" }
local STATUS = { 200, 200, 200, 201, 204, 304, 400, 401, 403, 404, 404, 409, 500, 503 }
local function pathgen()
    local cat = "/api/catalog/v1/c" .. R(1, 3)
    local x = R(1, 22)
    if x == 1 then return "/api/management/v1/principal-roles/pr" .. R(1, 400) .. "/catalog-roles/c1"
    elseif x == 2 then return "/api/management/v1/principal-roles"
    elseif x == 3 then return "/api/management/v1/catalogs/c1/catalog-roles/r" .. R(1, 300) .. "/grants"
    elseif x == 4 then return "/api/management/v1/catalogs/c1/catalog-roles"
    elseif x == 5 then return "/api/catalog/v1/oauth/tokens"
    elseif x == 6 then return "/api/catalog/v1/config?warehouse=c1"
    elseif x == 7 then return cat .. "/tables/rename"
    elseif x == 8 then return cat .. "/transactions/commit"
    elseif x == 9 then return cat .. "/namespaces/n" .. R(1, 5) .. "/register"
    elseif x == 10 then return cat .. "/namespaces/n" .. R(1, 5) .. "/properties"
    elseif x == 11 then return cat .. "/namespaces/n" .. R(1, 5) .. "%1Fm/tables/t" .. R(1, 900) .. "/metrics"
    elseif x == 12 then return cat .. "/namespaces/n" .. R(1, 5) .. "/views/v" .. R(1, 50)
    elseif x == 13 then return cat .. "/namespaces/n" .. R(1, 5) .. "/tables"
    elseif x == 14 then return cat .. "/namespaces/n" .. R(1, 5)
    elseif x == 15 then return cat .. "/namespaces"
    elseif x == 16 then return "/api/management/v1/catalogs/c" .. R(1, 9)
    elseif x == 17 then return "/api/management/v1/principals/p" .. R(1, 300) .. "/rotate"
    elseif x == 18 then return "/api/management/v1/principals"
    elseif x == 19 then return "/scan/" .. R(1, 1e6) .. "?q=" .. R(1, 9)
    elseif x == 20 then return cat .. "/namespaces//tables/x"
    elseif x == 21 then return "/q/health"
    else return cat .. "/namespaces/n1/tables/t" .. R(1, 20) end
end
n, bad, emitted, reports = 0, 0, 0, 0
local now = 1789500000
step("polaris.report", { tick = "x", _now_override = now })
local rids = {}
for i = 1, N do
    local k = R(1, 1000)
    if k <= TICK then
        now = now + (R(1, 20) == 1 and R(100, 400) or R(1, 6))   -- 가끔 긴 공백: 고아 만료·잠자기
        step("polaris.report", { tick = "x", _now_override = now })
    else
        local rid
        if R(1, 10) > 1 then
            if #rids > 0 and R(1, 3) == 1 then rid = rids[R(1, #rids)] else rid = "r" .. R(1, 1e9); rids[#rids + 1] = rid end
            if #rids > 5000 then rids = {} end
        end
        local lvl = ({ "INFO", "INFO", "INFO", "INFO", "INFO", "INFO", "DEBUG", "WARN", "ERROR" })[R(1, 9)]
        local rec
        if k <= 600 then
            local user = R(1, 8) == 1 and ("u" .. R(1, 3000)) or ("svc" .. R(1, 4))
            local msg
            if R(1, 60) == 1 then msg = ({ "garbage line", "", "1.2.3.4 - u [x] \"get / HTTP/1.1\" 200 1" })[R(1, 3)]
            else
                msg = string.format('10.0.0.%d - %s [16/Sep/2026:00:00:05 +0000] "%s %s HTTP/1.1" %d %s',
                    R(1, 9), user, METHODS[R(1, #METHODS)], pathgen(), STATUS[R(1, #STATUS)],
                    R(1, 5) == 1 and "-" or tostring(R(0, 5000)))
            end
            rec = { loggerName = A, level = lvl, message = R(1, 200) == 1 and 42 or msg }
        else
            local lg = R(1, 40) == 1 and ("org.x.L" .. R(1, 80)) or LOGGERS[R(1, #LOGGERS)]
            local msg
            local m = R(1, 8)
            if m == 1 then msg = "Successfully committed to table c" .. R(1, 3) .. ".n" .. R(1, 5) .. ".t" .. R(1, 20) .. " in " .. R(1, 90) .. " ms"
            elseif m == 2 then msg = "Successfully committed to view c1.a.b.v" .. R(1, 5) .. " in " .. R(1, 90) .. " ms"
            elseif m == 3 then msg = "Created new principal {clientId: x, clientSecret: " .. (R(1, 2) == 1 and "*" or "s3cr3t") .. "}"
            elseif m == 4 then msg = "Successfully committed to table short in 3 ms"
            else msg = "Handling runtimeException " .. R(1, 1e6) end
            rec = { loggerName = (R(1, 100) == 1) and nil or lg, level = lvl, message = msg }
        end
        if rid then rec.mdc = { requestId = rid } end
        rec._time = string.format("2026-09-16T00:%02d:%02d.%03dZ", R(0, 59), R(0, 59), R(0, 999))
        rec._now_override = now
        step("polaris.logs", rec)
    end
end
step("polaris.report", { tick = "x", _now_override = now + 3600 })
local cv = {}
for k, v in pairs(COV) do cv[#cv + 1] = k .. "=" .. v end
table.sort(cv)
print("fuzz coverage (windows or docs where it was non-zero): " .. table.concat(cv, " "))
print(string.format("fuzz:  %d calls, %d emitting, %d reports, %d diffs", n, emitted, reports, bad))
if bad > 0 then os.exit(1) end
print("EQUIVALENT")
