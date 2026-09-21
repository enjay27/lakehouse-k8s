-- classify() 후보 비교: 결과 동일성(차등) + 속도. 입력 = 실제 경로 + 경계 사례.
--   luajit logging/candidates/bench-classify.lua /tmp/paths.txt
-- 현재 규칙표를 그대로 복사한다 (fluent-bit/polaris_access_log.lua RESOURCE_PATTERNS, v5).
local RESOURCE_PATTERNS = {
    { kind = "principal-role", pattern = "^.-/principal%-roles/[^/]+" },
    { kind = "collection",     pattern = "^.-/principal%-roles$" },
    { kind = "catalog-role",   pattern = "^.-/catalog%-roles/[^/]+" },
    { kind = "collection",     pattern = "^.-/catalog%-roles$" },
    { kind = "auth",           pattern = "^.-/oauth/tokens$" },
    { kind = "config",         pattern = "^.-/v1/config$" },
    { kind = "table",          pattern = "^.-/tables/rename$" },
    { kind = "view",           pattern = "^.-/views/rename$" },
    { kind = "transaction",    pattern = "^.-/transactions/commit$" },
    { kind = "collection",     pattern = "^.-/namespaces/[^/]+/register$" },
    { kind = "namespace",      pattern = "^.-/namespaces/[^/]+/properties$" },
    { kind = "table",          pattern = "^.-/namespaces/[^/]+/tables/[^/]+" },
    { kind = "view",           pattern = "^.-/namespaces/[^/]+/views/[^/]+" },
    { kind = "collection",     pattern = "^.-/namespaces/[^/]+/tables$" },
    { kind = "collection",     pattern = "^.-/namespaces/[^/]+/views$" },
    { kind = "namespace",      pattern = "^.-/namespaces/[^/]+$" },
    { kind = "collection",     pattern = "^.-/namespaces$" },
    { kind = "catalog",        pattern = "^.-/catalogs/[^/]+" },
    { kind = "collection",     pattern = "^.-/catalogs$" },
    { kind = "principal",      pattern = "^.-/principals/[^/]+" },
    { kind = "collection",     pattern = "^.-/principals$" },
}

-- 0. 현재 (v5)
local function classify_current(path)
    for _, r in ipairs(RESOURCE_PATTERNS) do
        local span = path:match(r.pattern)
        if span then return span, r.kind end
    end
    return path, "other"
end

-- B. 같은 패턴, 앞에 plain find 가드. 가드 문자열은 패턴이 반드시 포함하는 리터럴이므로
--    "가드 실패 ⇒ 패턴 실패" 가 구성상 성립한다 — 결과가 달라질 수 없다.
local function lit_of(pat)                   -- "^.-/principal%-roles/[^/]+" -> "/principal-roles"
    local body = pat:gsub("^%^%.%-", ""):gsub("%$$", "")
    local lit = body:match("^([^%[]*)"):gsub("%%(.)", "%1")
    return lit
end
local GUARDED = {}
for i, r in ipairs(RESOURCE_PATTERNS) do GUARDED[i] = { kind = r.kind, pattern = r.pattern, lit = lit_of(r.pattern) } end
local find, match = string.find, string.match
local function classify_guarded(path)
    for i = 1, #GUARDED do
        local r = GUARDED[i]
        if find(path, r.lit, 1, true) then
            local span = match(path, r.pattern)
            if span then return span, r.kind end
        end
    end
    return path, "other"
end

-- C. 현재 + 경로 캐시 (상한 있음; 실제 파일에서는 윈도우마다 비움)
local cache, n_cache = {}, 0
local function classify_cached(path)
    local c = cache[path]
    if c then return c[1], c[2] end
    local k, kind = classify_current(path)
    if n_cache < 5000 then cache[path] = { k, kind }; n_cache = n_cache + 1 end
    return k, kind
end

-- D. B + C
local cache2, n_cache2 = {}, 0
local function classify_guarded_cached(path)
    local c = cache2[path]
    if c then return c[1], c[2] end
    local k, kind = classify_guarded(path)
    if n_cache2 < 5000 then cache2[path] = { k, kind }; n_cache2 = n_cache2 + 1 end
    return k, kind
end

-- A. 세그먼트 토크나이저 (한 번 분할, 규칙은 세그먼트 비교)
local function segs(path)
    local s, e, n = {}, {}, 0
    local pos = 1
    local len = #path
    while true do
        local j = find(path, "/", pos, true)
        n = n + 1
        s[n] = pos
        if j == nil then e[n] = len; break end
        e[n] = j - 1
        pos = j + 1
    end
    return s, e, n
end
local function classify_tokens(path)
    local s, e, n = segs(path)
    local function seg(i) return path:sub(s[i], e[i]) end
    local function nonempty(i) return i <= n and e[i] >= s[i] end
    local function first_pair(name)             -- ^.-/name/[^/]+
        for i = 2, n - 1 do
            if seg(i) == name and nonempty(i + 1) then return path:sub(1, e[i + 1]) end
        end
    end
    local function ends(...)                    -- ^.-/a/b$ (리터럴만)
        local t = { ... }
        local k = #t
        if n - k + 1 < 2 then return false end
        for x = 1, k do if seg(n - k + x) ~= t[x] then return false end end
        return true
    end
    local function ends_ns(last)                -- ^.-/namespaces/[^/]+/last$
        return n >= 4 and seg(n) == last and nonempty(n - 1) and seg(n - 2) == "namespaces"
    end
    local k
    k = first_pair("principal-roles"); if k then return k, "principal-role" end
    if ends("principal-roles") then return path, "collection" end
    k = first_pair("catalog-roles"); if k then return k, "catalog-role" end
    if ends("catalog-roles") then return path, "collection" end
    if ends("oauth", "tokens") then return path, "auth" end
    if ends("v1", "config") then return path, "config" end
    if ends("tables", "rename") then return path, "table" end
    if ends("views", "rename") then return path, "view" end
    if ends("transactions", "commit") then return path, "transaction" end
    if ends_ns("register") then return path, "collection" end
    if ends_ns("properties") then return path, "namespace" end
    for _, obj in ipairs({ { "tables", "table" }, { "views", "view" } }) do
        for i = 2, n - 3 do
            if seg(i) == "namespaces" and nonempty(i + 1) and seg(i + 2) == obj[1] and nonempty(i + 3) then
                return path:sub(1, e[i + 3]), obj[2]
            end
        end
    end
    if ends_ns("tables") then return path, "collection" end
    if ends_ns("views") then return path, "collection" end
    if n >= 3 and seg(n - 1) == "namespaces" and nonempty(n) then return path, "namespace" end
    if ends("namespaces") then return path, "collection" end
    k = first_pair("catalogs"); if k then return k, "catalog" end
    if ends("catalogs") then return path, "collection" end
    k = first_pair("principals"); if k then return k, "principal" end
    if ends("principals") then return path, "collection" end
    return path, "other"
end
-- NOTE: 규칙 12 는 "첫 namespaces 뒤 tables" 가 아니라 ".-" 가 허용하는 첫 위치다 — 위 루프는
-- tables 규칙 전체를 먼저 훑고 views 를 훑는다(패턴 순서와 같다).

-- 입력
local paths = {}
for l in io.lines(arg[1]) do paths[#paths + 1] = l:match("^[^?]*") end
local EDGE = {
    "", "/", "//", "/api", "/api/catalog/v1/c/namespaces", "/api/catalog/v1/c/namespaces/",
    "/api/catalog/v1/c/namespaces//tables/t", "/api/catalog/v1/c/namespaces/a%1Fb/tables/t/metrics",
    "/api/catalog/v1/c/namespaces/n/tables/", "/api/catalog/v1/c/namespaces/n/tables",
    "/api/catalog/v1/c/namespaces/n/views/v", "/api/catalog/v1/c/namespaces/n/register",
    "/api/catalog/v1/c/namespaces/n/properties", "/api/catalog/v1/c/namespaces/namespaces/tables/t",
    "/api/catalog/v1/c/namespaces/n/namespaces/m/tables/t", "/api/catalog/v1/c/tables/rename",
    "/api/management/v1/principal-roles/pr/catalog-roles/c", "/api/management/v1/principal-roles/",
    "/api/management/v1/principal-roles", "principal-roles/x", "/principal-roles/x",
    "/api/management/v1/catalogs/c/catalog-roles/r/grants", "/api/management/v1/catalogs/c/catalog-roles",
    "/api/management/v1/catalogs//catalog-roles/r", "/api/management/v1/catalogs/", "/api/management/v1/catalogs",
    "/api/management/v1/principals/p/rotate", "/api/management/v1/principals", "/oauth/tokens", "oauth/tokens",
    "/api/catalog/v1/oauth/tokens/", "/v1/config", "/api/catalog/v1/config", "/api/catalog/v1/c/transactions/commit",
    "/api/catalog/v1/c/namespaces/n/tables/t/tables/rename", "/q/health", "/api/catalog/v1/c/namespaces/n/views",
    "/api/catalog/v1/c/namespaces/ns/tables/x/principals/y", "/a/namespaces/b", "/namespaces/b",
}
for _, p in ipairs(EDGE) do paths[#paths + 1] = p end

local V = { current = classify_current, guarded = classify_guarded, cached = classify_cached,
            guarded_cached = classify_guarded_cached, tokens = classify_tokens }
local order = { "current", "guarded", "cached", "guarded_cached", "tokens" }
local diffs = {}
for _, name in ipairs(order) do
    local nd = 0
    for _, p in ipairs(paths) do
        local k0, t0 = classify_current(p)
        local k1, t1 = V[name](p)
        if k0 ~= k1 or t0 ~= t1 then
            nd = nd + 1
            if nd <= 5 then print(string.format("  DIFF %-15s %q  cur=%s/%s  new=%s/%s", name, p, k0, t0, tostring(k1), tostring(t1))) end
        end
    end
    diffs[name] = nd
end
print(string.format("inputs: %d paths (%d real + %d edge)", #paths, #paths - #EDGE, #EDGE))

local ROUNDS = tonumber(arg[2]) or 2000
for _, name in ipairs(order) do
    cache, n_cache, cache2, n_cache2 = {}, 0, {}, 0
    local f = V[name]
    collectgarbage(); collectgarbage()
    local t = os.clock()
    -- 캐시는 라운드마다 비운다 = 윈도우 하나에 이 경로 집합이 한 번씩 (실데이터 적중률 그대로)
    for _ = 1, ROUNDS do
        cache, n_cache, cache2, n_cache2 = {}, 0, {}, 0
        for i = 1, #paths do f(paths[i]) end
    end
    local dt = os.clock() - t
    print(string.format("  %-15s diffs=%d  %.0f ns/call", name, diffs[name], dt / (ROUNDS * #paths) * 1e9))
end
