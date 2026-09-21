-- 필터 전체 CPU 비교 (Lua 안에서만): 현재 = polaris_access_log + polaris_noise_filter, 후보 = 병합형.
--   luajit logging/candidates/bench-refactor.lua fluent-bit/polaris_access_log.lua \
--          logging/candidates/polaris_access_log.refactor.lua /tmp/tier1_all.lua [rounds]
-- 입력: readout 3개의 tier-1 레코드 2,136건을 라운드마다 새로 복사해(측정 제외) 넣는다.
-- 시각은 레코드당 1/580 초씩 증가 (운영 부하 추정 580 lines/s), 5초마다 틱, 30초 윈도우.
-- ⚠ 측정하지 않는 것: Fluent Bit 이 Lua 호출마다 하는 msgpack <-> Lua 테이블 변환 (C 코드).
--   R1 의 주 이득이 거기에 있고, 그것은 phase 3.1 부하 테스트에서 파드 CPU 로만 잴 수 있다.
local function load(path)
    local f = assert(loadstring(assert(io.open(path)):read("*a"), "@" .. path))
    local env = setmetatable({}, { __index = _G }); setfenv(f, env); f(); return env
end
local data = dofile(arg[3])
local ROUNDS = tonumber(arg[4]) or 50
local function run(env, split)
    local nf, al = env.polaris_noise_filter, env.polaris_access_log
    local now, last_tick = 1789500000, 1789500000
    nf("polaris.report", 0, { tick = "x", _now_override = now })
    local recs = {}
    local total = 0
    collectgarbage(); collectgarbage()
    local gc0 = collectgarbage("count")
    local elapsed = 0
    for _ = 1, ROUNDS do
        for i, r in ipairs(data) do       -- 측정 제외: 입력 복사
            recs[i] = { loggerName = r.loggerName, level = r.level, _msg = r._msg, _time = r._time,
                        mdc = r.mdc and { requestId = r.mdc.requestId } or nil }
        end
        local t = os.clock()
        for i = 1, #recs do
            local rec = recs[i]
            now = now + 1 / 580
            rec._now_override = math.floor(now)
            if now - last_tick >= 5 then
                last_tick = now
                nf("polaris.report", 0, { tick = "x", _now_override = math.floor(now) })
            end
            if split then local _, _, r2 = al("polaris.logs", 0, rec); rec = r2 or rec end
            nf("polaris.logs", 0, rec)
        end
        elapsed = elapsed + (os.clock() - t)
        total = total + #recs
    end
    return elapsed, total
end
for pass = 1, 2 do
    local e1, n1 = run(load(arg[1]), true)
    local e2, n2 = run(load(arg[2]), false)
    print(string.format("pass %d  current %6.0f ns/record   candidate %6.0f ns/record   (%.2fx, %d records each)",
        pass, e1 / n1 * 1e9, e2 / n2 * 1e9, e1 / e2, n1))
end
