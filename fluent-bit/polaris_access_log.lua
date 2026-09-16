-- =====================================================================================
-- polaris_access_log.lua — Polaris 감사 로그 Fluent Bit Lua 필터 (정책 v5 / 리포트 스키마 v5)
-- =====================================================================================
--
-- 한 파일에 함수 두 개, FILTER 도 두 개로 건다.
--
--   polaris_access_log    Match polaris.logs   액세스 라인(_msg)을 필드로 분해
--   polaris_noise_filter  Match polaris.*      적재 판정 + 윈도우 집계 + 리포트 생성
--
-- 두 번째 필터가 polaris.logs 가 아니라 polaris.* 를 매치하는 이유: 리포트 틱(dummy
-- INPUT, Tag polaris.report)도 "같은 필터 인스턴스" 를 지나야 한다. Lua 상태(카운터)는
-- 인스턴스 단위라서, 틱이 다른 인스턴스로 가면 비어 있는 카운터를 보고하게 된다.
--
-- 런타임: Fluent Bit 내장 LuaJIT (Lua 5.1 문법). `//`, `table.unpack`, 정수 나눗셈 등
-- 5.3+ 기능은 쓰지 않는다. 테스트는 luajit / lua5.1 로 돌린다.
--
-- ── v4 → v5 변경 요약 (2026-09-16, logging/PLAN-audit-log-todo-2026-09-16.md 2.1–2.3) ──
--   1. 404 는 적재하지 않고 집계만 한다 (결정: Kade 2026-09-16). 액세스 라인은 errors /
--      errors_4xx 에 반영되고 summary.counted_404 로 세어진다.
--   2. 404 요청이 남긴 애플리케이션 로그(예외 사유, grant/assign 시도)도 버린다. 판단은
--      mdc.requestId 로 한다: 허용 목록의 앱 로그를 요청 ID 별로 "보류" 했다가 같은 ID 의
--      액세스 라인이 오면 상태를 보고 함께 내보내거나 함께 버린다 (§ 요청 ID 보류).
--   3. /namespaces/{ns}/register 분류 규칙 추가 (kind collection).
--   4. Lua 는 values 가 아니라 별도 ConfigMap(fluent-bit/kustomization.yaml)으로 배포되고
--      hot reload 로 교체된다. reload 하면 이 파일의 모든 상태(윈도우 카운터, 보류 목록)가
--      초기화된다 — 다음 리포트 행은 partial, report_seq 는 1 부터.
--
-- ── v3 → v4 변경 요약 (logging/PLAN-audit-allowlist-2026-09-15.md) ─────────────────
--   1. 규칙 2: 애플리케이션 로그를 "전부 적재" 에서 "허용 목록(APP_ALLOW)만 적재" 로.
--      목록 밖의 로그는 버리되 logger 별로 세어 report_type "app_dropped" 로 보고한다.
--   2. `Successfully committed to table|view <id> in N ms` 를 버리기 전에 수확해서,
--      해당 table/view 리소스 행에 commit_count / commit_ms_sum / _min / _max 로 붙인다.
--   3. zero-carry 삭제: 요청 0 이고 커밋도 없는 행은 내보내지 않는다.
--      summary 의 carried_rows 필드도 함께 제거.
--   4. 자격증명 가드: 적재되는 레코드의 _msg 에 마스킹되지 않은 clientSecret 이 있으면
--      값을 <redacted> 로 바꾸고 secret_redacted=true 를 단다.
--   summary 행은 유지한다 (결정 D1 — 완결성 불변식이 여기에만 있다).
-- =====================================================================================


-- ─────────────────────────────────────────────────────────────────────────────────────
-- 1단계: polaris_access_log — 액세스 라인 파싱
-- ─────────────────────────────────────────────────────────────────────────────────────
-- loggerName 이 io.quarkus.http.access-log 인 레코드만 건드린다. 나머지는 그대로 통과.
--
-- 입력 _msg 형식 (Quarkus 패턴 %h %l %u %t "%r" %s %b):
--   192.168.194.1 - root [03/Sep/2026:06:37:47 +0000] "DELETE /api/... HTTP/1.1" 404 133
--   client_ip     |  user   시각(버림)                 method  path   버전(버림) status size
--                 %l, 항상 "-", 버림
--
-- _msg 원문은 지우지 않는다. 파싱이 틀렸을 때 읽을 수 있는 유일한 근거다.

local ACCESS_LOGGER = "io.quarkus.http.access-log"

-- 정규식이 아니라 Lua 패턴이다. %S 공백 아닌 문자, %u 대문자, %d 숫자, %[ 는 리터럴 [.
-- 따옴표 안의 HTTP 버전 토큰은 [^"]* 가 캡처 없이 먹는다.
local PATTERN = '^(%S+) %S+ (%S+) %[[^%]]*%] "(%u+) (%S+)[^"]*" (%d+) (%S+)'

function polaris_access_log(tag, timestamp, record)
    if record["loggerName"] ~= ACCESS_LOGGER then
        return 0, timestamp, record            -- 0 = 변경 없음, 그대로 통과
    end

    local msg = record["_msg"]
    if type(msg) ~= "string" then
        record["access_log_parse_error"] = true
        return 2, timestamp, record
    end

    local ip, user, method, path, status, size = string.match(msg, PATTERN)

    if ip == nil then
        -- 조용히 실패하지 않는다. 이 logger 의 라인이 파싱되지 않는다는 것은 로그 패턴이
        -- 바뀌었다는 뜻이고, access_log_parse_error:true 로 찾을 수 있어야 한다.
        record["access_log_parse_error"] = true
        return 2, timestamp, record
    end

    record["client_ip"]           = ip
    record["user_principal_name"] = user
    record["http_method"]         = method
    record["api_path"]            = path
    record["http_status"]         = tonumber(status)
    -- CLF 의 %b 는 본문 0바이트를 "-" 로 쓴다. "알 수 없음" 이 아니라 0 이다.
    record["response_size"]       = tonumber(size) or 0

    -- 1 이 아니라 2: 1 은 반환한 timestamp 까지 적용하라는 뜻이라 Lua double 로 한 번
    -- 왕복한다. 2 는 "레코드만 바뀜, 시각은 그대로" 이고 실제로 일어난 일이 그것이다.
    return 2, timestamp, record
end


-- ─────────────────────────────────────────────────────────────────────────────────────
-- 2단계: polaris_noise_filter — 무엇을 적재할지 판정하고, 나머지는 센다
-- ─────────────────────────────────────────────────────────────────────────────────────
-- 위에서부터 순서대로 평가하며, 먼저 일치한 규칙이 이긴다.
--
--   0. 리포트 틱 (tag polaris.report) ................ 윈도우가 넘어가면 리포트로 치환
--   *  모든 레코드: 마스킹 안 된 clientSecret 은 <redacted> 로 치환 (적재 전 가드)
--   1. level ERROR / WARN ............................ 적재 (허용 목록과 무관)
--   2. 액세스 로그가 아닌 레코드
--        2a. `Successfully committed to table|view` .. 커밋 시간을 해당 행에 집계
--        2b. loggerName 이 APP_ALLOW 에 있음 ........ 적재
--        2c. 그 외 ................................... logger 별로 세고 버림 (app_dropped)
--   --- 모든 액세스 라인은 여기서 "판정 전에" 먼저 집계된다 ---
--        2b'. 단, mdc.requestId 가 있으면 즉시 적재하지 않고 요청 ID 별로 보류 → 규칙 3'
--   3'. http_status == 404 ............................ 집계만 (counted_404). 같은 요청 ID 로
--                                                       보류된 앱 로그도 함께 버림 (app_dropped_404)
--   3. http_status >= 400 또는 파싱 실패 ............ 적재 — 전건, 상한 없음
--   4. PUT / DELETE / PATCH .......................... 적재 — 전건
--   5. /api/management/ 하위 POST .................... 적재 — 전건
--      그 외 경로의 POST ............................  집계만
--   6. GET / HEAD, 2xx ...............................  집계만
--   7. 그 외 ......................................... 적재
--
-- 보장하는 것:
--   * 인가 실패 100% 보존 — 모든 401·403 은 규칙 3 에 의해 전문 문서로 남는다.
--   * 액세스 라인이 적재되는 요청의 앱 로그는 그 액세스 라인과 "같은 반환" 으로 나간다.
--   * 신원·권한 변경 100% 보존 — management POST, 모든 PUT, 모든 DELETE.
--   * "적재하지 않음 ⇒ 집계됨" — 버린 액세스 라인은 리소스/principal 행에, 버린
--     애플리케이션 로그는 app_dropped 행에 반드시 숫자로 남는다.
--
-- 규칙 5 의 management/catalog 분리는 임의가 아니다. Polaris 에서 POST 는 "생성" 동사다
-- (create_principal, create_principal_role, create_catalog_role, reset_credentials).
-- POST 를 통째로 집계만 하면 principal 이 "생성될 때는 안 보이고 삭제될 때만 보이는"
-- 감사 비대칭이 생긴다. 반대로 catalog POST(create_table, commit, rename, report_metrics,
-- oauth/tokens)는 데이터 플레인 반복 트래픽이므로 집계만 한다.
--
-- 규칙 1 에 "deprecated config" 제외 조항이 없는 이유: polaris/values.yaml 에서
-- io.quarkus.config 가 OFF 라 애초에 출력되지 않는다 (2026-09-04 측정 0건).


-- ── 튜닝 값 ────────────────────────────────────────────────────────────────────────────
local REPORT_TAG     = "polaris.report"
local REPORT_APP     = "polaris-shipper-report"

-- 스키마 버전. 필드의 "의미" 가 바뀌면 올린다. 모든 대시보드/쿼리는 이 값으로 필터할 것.
--   v4 (2026-09-15): report_type "app_dropped" 추가, table/view 행에 commit_* 추가,
--                    zero-carry 제거(carried_rows 삭제), summary 에 app_dropped_total 추가.
--   v3 (2026-09-09): last_read_bytes/last_write_bytes, api_kind, grant 의 롤 행 귀속.
-- 새 숫자 필드는 반드시 values.yaml FILTER 3 의 type_int_key 에도 넣어야 한다.
-- 빠지면 문자열로 저장되고, 숫자 범위 쿼리가 "조용히" 0건을 반환한다.
--   v5 (2026-09-16): 404 집계만 + 같은 요청의 앱 로그 폐기, summary 에 counted_404 /
--                    app_dropped_404 / held_pending / held_orphans 추가, register 분류.
local SCHEMA_VERSION = 5

-- 리포트 윈도우 길이(초). values.yaml 의 틱 INPUT Interval_Sec 과 짝이다.
-- 정상 운영 1800 (매시 :00 / :30, KST 는 UTC+9 정수 시간이라 경계가 같다).
-- 검증 구간에는 30 / Interval_Sec 5 로 낮춰 쓴다. 둘은 항상 같이 바꾼다.
local WINDOW_SECONDS = 30     -- ⚠ 임시 검증값 (2026-09-04~). 운영값은 1800 이며, 되돌리는 것이
                               -- 컷오버의 마지막 단계다 (틱 INPUT 과 함께). 이 상수 외에 읽는 곳 없음.

-- ── 규칙 2: 애플리케이션 로그 허용 목록 ────────────────────────────────────────────────
-- logger 단위로 허용한다. 메시지 접두어 단위로 하지 않는 이유: PolarisServiceImpl 에
-- 업그레이드로 새 메시지("Updating ..." 등)가 생기면 접두어 목록은 그것을 조용히 버린다.
-- 이 두 logger 는 본질적으로 요청당 0~1줄이라 logger 단위로 전부 받아도 양이 적다.
--
-- 2026-09-15 export(run 1789436277) 기준 판정:
--   적재  IcebergExceptionMapper   180  4xx/5xx 의 "이유" (Handling runtimeException ...)
--   적재  PolarisServiceImpl        75  grant/revoke, create, assign — "누가 무엇을 바꿨나"
--   버림  IcebergCatalogHandler     61  Initializing non-federated catalog (거의 매 요청)
--   버림  BaseMetastoreCatalog      37  Table properties set/enforced ...: {}
--   버림  CatalogUtil               30  Loading custom FileIO implementation
--   버림  IcebergCatalog            24  Refreshing table / Successfully committed (→ 2a 수확)
--   버림  BaseMetastoreViewCatalog   6  View properties set/enforced ...: {}
--   버림  ObjectMapperCustomizer     3  Limiting request body size (기동 시)
-- 적재된 두 logger 의 문서는 mdc.requestId 로 액세스 문서와 100% 조인된다 (측정).
local APP_ALLOW = {
    ["org.apache.polaris.service.exception.IcebergExceptionMapper"] = true,
    ["org.apache.polaris.service.admin.PolarisServiceImpl"]         = true,
}

-- app_dropped 행에 올릴 logger 이름 수 상한. 넘치면 "__other__" 한 행으로 합친다.
-- logger 이름은 코드가 정하므로 사실상 유한하지만, 상한 없는 테이블은 두지 않는다.
local REPORT_MAX_DROPPED_LOGGERS = 50

-- ── 요청 ID 보류 (v5) ──────────────────────────────────────────────────────────────────
-- 예외 사유·grant 로그는 액세스 라인보다 "먼저" 찍힌다 (2026-09-16 실측: 앱 로그 210건 중
-- 207건이 앞, 간격 최대 11 ms). 그 시점에는 응답 코드를 모르므로, 허용 목록의 앱 로그를
-- mdc.requestId 별로 잡아 두었다가 같은 ID 의 액세스 라인이 오면 결정한다.
--   * 404          → 보류분도 버린다 (app_dropped_404 로 셈)
--   * 그 외        → 보류분을 액세스 라인과 같은 반환으로 내보낸다
--   * 액세스 뒤에 온 앱 로그 → STATUS_MEMO 에 남은 상태로 즉시 판정 (측정: 3건, 같은 ID 재사용)
--   * requestId 없음 → 보류하지 않고 즉시 적재 (v4 동작)
-- 여러 레코드를 한 번에 반환하면 Fluent Bit 은 하나의 timestamp 를 쓴다: 보류분의 @timestamp 는
-- 액세스 라인 시각으로 수 ms 이동한다. 원래 시각은 _time 필드에 그대로 남는다.
-- ⚠ 요청 ID 는 클라이언트가 보낸 Polaris-Request-Id 헤더다. 헤더 없는 요청에 Polaris 가 ID 를
--   붙이는지는 미측정 — 붙이지 않으면 그 요청의 앱 로그는 보류 없이 적재된다(404 여도).
local HOLD_MAX_SECONDS    = 30      -- 짝을 못 만난 보류분은 이 시간 뒤 다음 레코드와 함께 적재
local HOLD_MAX_RECORDS    = 10000   -- 상한. 넘치면 가장 오래된 보류분부터 적재
local STATUS_MEMO_SECONDS = 30      -- 액세스 라인 뒤에 온 앱 로그를 판정하기 위한 상태 기억
local STATUS_MEMO_MAX     = 20000

-- ── 2a: 커밋 시간 수확 ─────────────────────────────────────────────────────────────────
-- IcebergCatalog 가 커밋 성공 후 남기는 라인:
--   Successfully committed to table apimatrix_cat.probe_ns.probe_tbl in 20 ms
--   Successfully committed to view  apimatrix_cat.probe_ns.vw2       in 32 ms
-- 이 숫자는 "요청 지연" 이 아니라 Iceberg 커밋 시간이다 (메타데이터 파일 쓰기 + 메타스토어
-- CAS). 인증·파싱·응답은 포함되지 않고, 실패한 커밋은 로그가 없으므로 성공 건만 집계된다.
-- 필드 이름을 commit_ms_* 로 한 이유가 이것이다 — 요청 지연으로 읽히면 안 된다.
local COMMIT_LOGGER  = "org.apache.polaris.service.catalog.iceberg.IcebergCatalog"
local COMMIT_PATTERN = "^Successfully committed to (%a+) (%S+) in (%d+) ms"
local COMMIT_KINDS   = { table = "tables", view = "views" }
local CATALOG_API    = "/api/catalog/v1/"
-- 다단계 네임스페이스 구분자. 메시지에서는 "a.b", URL 에서는 "a%1Fb" (Iceberg REST 규약).
-- ⚠ 미검증: 2단계 네임스페이스로 키가 액세스 라인의 키와 같아지는지 테스트해야 한다.
--   다르면 실패하지 않고, 아무 요청도 붙지 않는 "유령 행" 이 조용히 하나 더 생긴다.
local NS_SEPARATOR   = "%1F"

-- ── 자격증명 가드 ──────────────────────────────────────────────────────────────────────
-- "Created new principal" 로그는 PrincipalWithCredentials 를 통째로 출력한다. 현재 Polaris 는
-- clientSecret 을 "*" 로 마스킹한다 (2026-09-15 export 4건 모두 확인). 그 마스킹이 회귀하면
-- 평문 시크릿이 30일 인덱스에 들어가므로, 믿지 않고 여기서 한 번 더 막는다.
local SECRET_PATTERN = "(clientSecret:%s*)([^%s]+)"

local MGMT_PREFIX    = "^/api/management/"

local READ_METHODS  = { GET = true, HEAD = true }
local WRITE_METHODS = { POST = true, PUT = true, DELETE = true, PATCH = true }
local KEEP_METHODS  = { PUT = true, DELETE = true, PATCH = true }

-- ── 리소스 분류 ────────────────────────────────────────────────────────────────────────
-- 카운터 키는 URL 이 아니라 "리소스" 다. /tables/t/metrics 와 /tables/t 는 같은 테이블이고,
-- 둘을 따로 세면 그 테이블의 모든 추이가 틀린다 (v2 에서 실측). 각 패턴은 쿼리스트링을
-- 뗀 경로에 대해 매치되고, 키는 "매치된 구간" 까지 잘린다. `.-` 는 게으른 매치라 카탈로그
-- 접두부가 키에 포함되므로, 다른 카탈로그의 같은 이름 테이블은 섞이지 않는다.
--
-- 순서가 곧 우선순위다:
--   * 롤 규칙이 가장 먼저. /catalog-roles/{cr}/grants 는 {cr} 행으로 접히므로 그 행의
--     writes 가 곧 "이 윈도우에 그 롤에 부여된 권한 수" 다.
--   * principal-role 이 catalog-role 보다 먼저. /principal-roles/{pr}/catalog-roles/{cat}
--     (할당)은 할당받는 principal role 에 귀속된다.
--   * rename 에는 /namespaces/ 구간이 없고, namespace 규칙은 끝이 고정($)이라
--     /namespaces/{ns}/properties 가 먼저 와야 한다.
--   * commitTransaction 은 다중 테이블 커밋이라 단일 테이블 신원이 없다 → 별도 kind.
--   * management 리소스(catalog, principal)는 롤 규칙 뒤, 맨 마지막.
-- 패턴 안의 '-' 는 반드시 %- 로 이스케이프한다. `%\-` 는 잘못된 이스케이프라 청크 로드
-- 자체가 실패한다 (2026-09-09 테스트에서 실제로 잡힘).
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
    -- v5: registerTable. 테이블 이름이 경로가 아니라 본문에 있으므로 컬렉션 행.
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

-- ── 행 수 상한 ─────────────────────────────────────────────────────────────────────────
-- 넘치면 요청은 "__other__" 한 행에 모인다. 합계는 정확하게 유지되고 키별 상세만 잘린다.
--
-- 오류 요청은 원칙적으로 새 행을 만들지 못한다(create=false). 없는 테이블 이름을 돌며
-- 두드리는 클라이언트가 키 공간을 채우지 못하게 하기 위해서다. 그 오류는 "__errors__"
-- 로 가고, 원본 문서는 규칙 3 에 의해 전건 남는다.
-- ⚠ 이 판정은 "그 순간 행이 있었나" 이다. 같은 윈도우 안이라도 첫 성공 "이전" 의 오류는
--   __errors__ 로, 이후의 오류는 그 행으로 간다 (run 1789460891 에서 실측).
--
-- 예외: 롤(catalog-role, principal-role)은 오류로도 행을 만들 수 있다. 거부된 grant 가
-- 곧 롤 행이 답해야 할 보안 질문이기 때문. 단 롤 이름도 클라이언트 입력이므로 별도 상한.
local ROLE_KINDS            = { ["catalog-role"] = true, ["principal-role"] = true }
local REPORT_MAX_ROLE_KEYS  = 100
local REPORT_MAX_RESOURCES  = 500
local REPORT_MAX_PRINCIPALS = 200
local REPORT_OTHER          = "__other__"
local REPORT_ERRORS         = "__errors__"


-- ── 헬퍼 ───────────────────────────────────────────────────────────────────────────────

-- 매치/키 생성 전에 쿼리스트링을 뗀다. api_path 필드 자체는 원문 그대로 둔다.
local function path_only(p)
    if type(p) ~= "string" then return "" end
    return p:match("^[^?]*") or p
end

-- api_kind 는 "어느 API 면인가" 이고, resource_kind("무엇인가")와 직교한다.
local function api_of(path)
    if path:find("^/api/management/") then return "management" end
    if path:find("^/api/catalog/")    then return "catalog"    end
    return "other"
end

-- 매치되는 규칙이 없으면 경로 전체를 키로, kind "other" 로 둔다. 버킷에 넣지 않는다 —
-- 새 API 가 생기면 무엇을 분류해야 하는지 그 행이 정확히 보여준다.
local function classify(path)
    for _, r in ipairs(RESOURCE_PATTERNS) do
        local span = path:match(r.pattern)
        if span then return span, r.kind end
    end
    return path, "other"
end

-- os.time() 은 리포트 윈도우에만 쓰고 레코드 시각에는 쓰지 않는다 (재생된 레코드를
-- 재-날짜 하지 않기 위해). _now_override 는 테스트 훅이며 dummy INPUT 은 설정하지 않는다.
local function now_seconds(record)
    return tonumber(record["_now_override"]) or os.time()
end

local function iso(t)
    return os.date("!%Y-%m-%dT%H:%M:%SZ", t)
end

-- "cat.ns1.ns2.tbl" → "/api/catalog/v1/cat/namespaces/ns1%1Fns2/tables/tbl"
-- 첫 조각 = 카탈로그(= Polaris URL prefix), 마지막 = 객체, 가운데 = 네임스페이스.
-- 조각이 3개 미만이면 키를 만들 수 없으므로 nil.
local function commit_key(kind, ident)
    local seg = COMMIT_KINDS[kind]
    if seg == nil then return nil end
    local parts = {}
    for p in string.gmatch(ident, "[^%.]+") do parts[#parts + 1] = p end
    if #parts < 3 then return nil end
    local ns = {}
    for i = 2, #parts - 1 do ns[#ns + 1] = parts[i] end
    return CATALOG_API .. parts[1] .. "/namespaces/" .. table.concat(ns, NS_SEPARATOR)
           .. "/" .. seg .. "/" .. parts[#parts]
end


-- ── 윈도우 카운터 ──────────────────────────────────────────────────────────────────────
-- 리포트를 낼 때마다 새로 연다. 각 리포트는 "그 윈도우의 증분" 이라 읽을 때 뺄셈이 필요 없다.
local counts, report_seq = nil, 0

-- 행 하나의 카운터.
--   reads = GET|HEAD, writes = POST|PUT|DELETE|PATCH, errors = status >= 400.
--   errors 는 reads/writes 와 의도적으로 겹친다. errors_4xx + errors_5xx 는 errors 와,
--   auth_denied(401|403)는 errors_4xx 와 겹친다 — 이 컬럼들을 더하는 대시보드는 틀린다.
--   last_* 와 commit_* 는 표본이 생길 때까지 nil. nil(부재) 과 0 은 다른 사실이다.
local function new_row()
    return { requests = 0, reads = 0, writes = 0, errors = 0, response_bytes = 0,
             errors_4xx = 0, errors_5xx = 0, auth_denied = 0,
             last_read_bytes = nil, last_write_bytes = nil,
             commit_count = nil, commit_ms_sum = nil, commit_ms_min = nil, commit_ms_max = nil }
end

-- v4: zero-carry 없음. 새 윈도우는 항상 빈 상태로 시작한다.
-- (v3 는 직전 윈도우의 활성 키를 0 으로 한 번 더 내보냈다. 요청이 0 으로 떨어진 것을
--  "데이터 포인트" 로 남기기 위해서였지만, 결정 D3 로 삭제. 이제 0 으로의 하락은 문서
--  "부재" 로 나타나므로, 대시보드는 빈 버킷을 0 으로 그리도록 설정해야 한다.)
local function new_window(idx, partial)
    return {
        window = idx, partial = partial and true or false,
        access_seen = 0, access_counted = 0, role_keys_forced = 0,
        counted_read = 0, counted_post = 0,
        errors_kept = 0, parse_errors = 0,
        resources = {}, kinds = {}, apis = {}, n_resources = 0, resources_over = 0,
        principals = {}, n_principals = 0, principals_over = 0,
        other_keys = {}, n_other_keys = 0,
        dropped = {}, n_dropped_loggers = 0, dropped_total = 0,
        counted_404 = 0, app_dropped_404 = 0, held_orphans = 0,
        min_time = nil, max_time = nil,
    }
end

-- create=false: 이미 있는 행이면 그 행, 없으면 __errors__ (귀속 정보 소실, 개수는 보존).
-- 상한 초과: __other__. resources_over 는 "접힌 요청 수", n_other_keys 는 "접힌 서로 다른
-- 키 수" — 한 URL 을 두드리는 고장 클라이언트와 스캐너를 구분하기 위해 둘 다 둔다.
local function touch_resource(key, kind, api, create)
    local r = counts.resources[key]
    if r ~= nil then return r end
    if not create then
        r = counts.resources[REPORT_ERRORS]
        if r == nil then
            r = new_row()
            counts.resources[REPORT_ERRORS] = r
            counts.kinds[REPORT_ERRORS] = "error"
            counts.apis[REPORT_ERRORS]  = "mixed"
            counts.n_resources = counts.n_resources + 1
        end
        return r
    end
    if counts.n_resources >= REPORT_MAX_RESOURCES then
        counts.resources_over = counts.resources_over + 1
        if counts.other_keys[key] == nil
           and counts.n_other_keys < REPORT_MAX_RESOURCES then
            counts.other_keys[key] = true
            counts.n_other_keys = counts.n_other_keys + 1
        end
        r = counts.resources[REPORT_OTHER]
        if r == nil then
            r = new_row()
            counts.resources[REPORT_OTHER] = r
            counts.kinds[REPORT_OTHER] = "other"
            counts.apis[REPORT_OTHER]  = "mixed"
            counts.n_resources = counts.n_resources + 1
        end
        return r
    end
    r = new_row()
    counts.resources[key] = r
    counts.kinds[key] = kind
    counts.apis[key]  = api
    counts.n_resources = counts.n_resources + 1
    return r
end

local function touch_principal(user)
    local p = counts.principals[user]
    if p ~= nil then return p end
    if counts.n_principals >= REPORT_MAX_PRINCIPALS then
        counts.principals_over = counts.principals_over + 1
        p = counts.principals[REPORT_OTHER]
        if p == nil then
            p = new_row()
            counts.principals[REPORT_OTHER] = p
            counts.n_principals = counts.n_principals + 1
        end
        return p
    end
    p = new_row()
    counts.principals[user] = p
    counts.n_principals = counts.n_principals + 1
    return p
end

-- 액세스 라인 한 건을 리소스 행과 principal 행 "양쪽" 에 센다.
-- 불변식: sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors
-- 두 여백이 같아야 한다. 대시보드는 이것으로 추이를 믿어도 되는지 먼저 확인한다.
local function count_record(record, method, path, user, status, bytes, parse_failed)
    if counts == nil then return end        -- 첫 틱 이전(기동 직후)은 윈도우가 없다
    counts.access_seen = counts.access_seen + 1

    -- 고정 형식·고정 존의 RFC3339 는 사전순 정렬이 곧 시간순이라 파싱이 필요 없다.
    -- 재생(replay)이 섞이면 min/max 폭이 윈도우보다 커져서 바로 드러난다.
    local t = record["_time"]
    if type(t) == "string" then
        if counts.min_time == nil or t < counts.min_time then counts.min_time = t end
        if counts.max_time == nil or t > counts.max_time then counts.max_time = t end
    end

    if parse_failed then
        counts.parse_errors = counts.parse_errors + 1
        return
    end

    local is_error = (status == nil or status >= 400)
    local key, kind = classify(path)

    local create = not is_error
    if (not create) and ROLE_KINDS[kind] then
        if counts.resources[key] ~= nil then
            create = true                            -- 이미 있는 키, 새 키 아님
        elseif counts.role_keys_forced < REPORT_MAX_ROLE_KEYS then
            counts.role_keys_forced = counts.role_keys_forced + 1
            create = true
        end
    end
    local api  = api_of(path)
    local rows = { touch_resource(key, kind, api, create), touch_principal(user) }
    for _, row in ipairs(rows) do
        row.requests = row.requests + 1
        if READ_METHODS[method] then
            row.reads = row.reads + 1
        elseif WRITE_METHODS[method] then
            row.writes = row.writes + 1
        end
        if is_error then
            row.errors = row.errors + 1
            -- status == nil 은 파싱 안 된 상태값. 오류이긴 하지만 4xx 는 아니다 —
            -- 4xx 로 세면 "클라이언트 오류" 가 파이프라인 자신의 실패를 흡수한다.
            if status ~= nil then
                if status >= 500 then
                    row.errors_5xx = row.errors_5xx + 1
                else
                    row.errors_4xx = row.errors_4xx + 1
                    if status == 401 or status == 403 then
                        row.auth_denied = row.auth_denied + 1
                    end
                end
            end
        end
        row.response_bytes = row.response_bytes + bytes

        -- 마지막 응답 크기, 윈도우 내 last-wins. 2xx 이고 크기 > 0 인 것만.
        -- 0 을 절대 쓰지 않으므로 "부재" 는 정확히 "이번 윈도우에 성공한 비어있지 않은
        -- 응답이 없었다" 는 뜻이 된다. 테이블 행에서 DROP(204, 빈 본문)은 자연히 빠지므로
        -- last_write_bytes 는 곧 마지막 커밋의 응답 크기다.
        if status ~= nil and status >= 200 and status < 300 and bytes > 0 then
            if READ_METHODS[method] then
                row.last_read_bytes = bytes
            elseif WRITE_METHODS[method] then
                row.last_write_bytes = bytes
            end
        end
    end
end

-- 2a. 커밋 라인을 해당 table/view 행에 집계한다.
-- create=true 가 맞다: 성공한 커밋은 그 객체가 실재한다는 증거다. 행 상한은 그대로 적용.
-- requests/reads/writes 는 건드리지 않는다 — 그것들은 액세스 라인만의 카운트로 남아야
-- 불변식이 유지된다. 그래서 트랜잭션으로만 바뀐 테이블은 requests 0 + commit_count N 행이 된다.
-- 커밋 로그는 액세스 라인보다 먼저 찍히므로, 경계 직전의 커밋은 다음 윈도우의 요청과
-- 다른 행 윈도우에 놓일 수 있다. 윈도우 합계 수준에서만 비교할 것.
local function count_commit(msg)
    if counts == nil or type(msg) ~= "string" then return end
    local kind, ident, ms = string.match(msg, COMMIT_PATTERN)
    if kind == nil then return end
    local key = commit_key(kind, ident)
    ms = tonumber(ms)
    if key == nil or ms == nil then return end
    local row = touch_resource(key, kind, "catalog", true)
    if row.commit_count == nil then
        row.commit_count, row.commit_ms_sum = 1, ms
        row.commit_ms_min, row.commit_ms_max = ms, ms
    else
        row.commit_count  = row.commit_count + 1
        row.commit_ms_sum = row.commit_ms_sum + ms
        if ms < row.commit_ms_min then row.commit_ms_min = ms end
        if ms > row.commit_ms_max then row.commit_ms_max = ms end
    end
end

-- 2c. 버린 애플리케이션 로그를 logger 별로 센다.
-- 허용 목록의 실패 모드는 "모르는 logger" 다. 이름이 바뀐 logger 나 새 logger 는 여기에
-- 숫자로 나타나야 한다 — app_dropped 에 새 org.apache.polaris.service.* 가 보이면 목록 검토.
local function count_dropped(record)
    if counts == nil then return end
    local name = record["loggerName"]
    if type(name) ~= "string" or name == "" then name = "-" end
    if counts.dropped[name] == nil then
        if counts.n_dropped_loggers >= REPORT_MAX_DROPPED_LOGGERS then
            name = REPORT_OTHER
        end
        if counts.dropped[name] == nil then
            counts.dropped[name] = 0
            counts.n_dropped_loggers = counts.n_dropped_loggers + 1
        end
    end
    counts.dropped[name] = counts.dropped[name] + 1
    counts.dropped_total = counts.dropped_total + 1
end

-- 적재 직전 자격증명 가드. "*" (Polaris 마스킹) 가 아니면 값을 치환한다.
-- 반환: 치환이 일어났으면 true.
local function redact_secret(record)
    local msg = record["_msg"]
    if type(msg) ~= "string" or not msg:find("clientSecret", 1, true) then return false end
    local hit = false
    local out = msg:gsub(SECRET_PATTERN, function(prefix, value)
        if value == "*" or value == "<redacted>" then return prefix .. value end
        hit = true
        return prefix .. "<redacted>"
    end)
    if hit then
        record["_msg"] = out
        record["secret_redacted"] = true
    end
    return hit
end


-- ── 리포트 생성 ────────────────────────────────────────────────────────────────────────
-- 네 가지 문서가 같은 봉투를 공유하고, _time 도 윈도우 끝으로 같다.
--   summary      윈도우당 정확히 1건. 완결성 불변식과 상한/틱 누락 카운터.
--   resource     리소스 키별 1건 (요청 > 0 또는 커밋 있음).
--   principal    호출 주체별 1건 (요청 > 0).
--   app_dropped  버린 logger 별 1건 (dropped > 0). zero-carry 없음 — 추이가 아니라 헬스 신호.
-- level 은 INFO 가 아니라 "REPORT" 로 둔다. 심각도가 아니라 스트림 선택자다.
-- ── 요청 ID 보류 상태 (윈도우와 무관, reload 전까지 유지) ────────────────────────────────
-- 큐는 head/tail 정수로 관리한다. 앞쪽이 nil 인 테이블에 `#` 을 쓰면 결과가 정의되지 않는다.
local held        = {}   -- rid -> { t = 처음 보류한 시각, recs = { record, ... } }
local held_q      = {}   -- [i] = { rid, t } 보류 순서 (오래된 것부터)
local held_q_head, held_q_tail = 1, 0
local held_count  = 0    -- 보류 중인 레코드 수
local memo        = {}   -- rid -> { status, t }
local memo_q      = {}
local memo_q_head, memo_q_tail = 1, 0
local memo_count  = 0

local function request_id_of(record)
    local m = record["mdc"]
    if type(m) == "table" then
        local rid = m["requestId"]
        if type(rid) == "string" and rid ~= "" then return rid end
    end
    return nil
end

local function remember_status(rid, status, now)
    if memo[rid] == nil then memo_count = memo_count + 1 end
    memo[rid] = { status = status, t = now }
    memo_q_tail = memo_q_tail + 1
    memo_q[memo_q_tail] = { rid = rid, t = now }
    while memo_q_head <= memo_q_tail do
        local e = memo_q[memo_q_head]
        if memo_count <= STATUS_MEMO_MAX and now - e.t <= STATUS_MEMO_SECONDS then break end
        local cur = memo[e.rid]
        if cur ~= nil and cur.t == e.t then memo[e.rid] = nil; memo_count = memo_count - 1 end
        memo_q[memo_q_head] = nil
        memo_q_head = memo_q_head + 1
    end
    if memo_q_head > memo_q_tail then memo_q, memo_q_head, memo_q_tail = {}, 1, 0 end
end

local function hold(rid, record, now)
    local h = held[rid]
    if h == nil then
        h = { t = now, recs = {} }
        held[rid] = h
        held_q_tail = held_q_tail + 1
        held_q[held_q_tail] = { rid = rid, t = now }
    end
    h.recs[#h.recs + 1] = record
    held_count = held_count + 1
end

local function release(rid)
    local h = held[rid]
    if h == nil then return nil end
    held[rid] = nil
    held_count = held_count - #h.recs
    return h.recs
end

-- 짝을 못 만난 보류분: HOLD_MAX_SECONDS 가 지났거나 상한을 넘으면 out 에 붙여 적재한다.
local function take_orphans(now, out)
    while held_q_head <= held_q_tail do
        local e = held_q[held_q_head]
        local h = held[e.rid]
        if h ~= nil and h.t == e.t then
            if held_count <= HOLD_MAX_RECORDS and now - e.t <= HOLD_MAX_SECONDS then break end
            for _, r in ipairs(h.recs) do
                r["held_orphan"] = true
                out[#out + 1] = r
            end
            if counts ~= nil then counts.held_orphans = counts.held_orphans + #h.recs end
            held_count = held_count - #h.recs
            held[e.rid] = nil
        end
        held_q[held_q_head] = nil
        held_q_head = held_q_head + 1
    end
    if held_q_head > held_q_tail then held_q, held_q_head, held_q_tail = {}, 1, 0 end
end

local function build_report(idx, windows_skipped)
    local starts, ends = iso(idx * WINDOW_SECONDS), iso((idx + 1) * WINDOW_SECONDS)
    report_seq = report_seq + 1
    local host = os.getenv("HOSTNAME") or "unknown"

    local function base(kind)
        return { app = REPORT_APP, level = "REPORT",
                 schema_version = SCHEMA_VERSION, report_type = kind,
                 report_seq = report_seq, hostname = host,
                 window_start = starts, window_end = ends,
                 window_seconds = WINDOW_SECONDS, _time = ends }
    end

    local out = {}
    local s = base("summary")
    local rows = {}
    local n_active_res, n_active_pri = 0, 0
    local tot_4xx, tot_5xx, tot_denied, tot_bytes = 0, 0, 0, 0

    for key, r in pairs(counts.resources) do
        -- 합계는 행 내보내기 여부와 무관하게 전부 더한다 (0 행은 어차피 0).
        tot_4xx    = tot_4xx + r.errors_4xx
        tot_5xx    = tot_5xx + r.errors_5xx
        tot_denied = tot_denied + r.auth_denied
        tot_bytes  = tot_bytes + r.response_bytes

        -- v4 / D3: 요청 0 이고 커밋도 없으면 행을 내지 않는다. zero-carry 가 없으므로
        -- 이런 행은 이론상 생기지 않지만, 방어적으로 한 번 더 거른다.
        if r.requests > 0 or r.commit_count ~= nil then
            local e = base("resource")
            e.resource       = key
            e.resource_kind  = counts.kinds[key] or "other"
            e.api_kind       = counts.apis[key]  or "other"
            e.requests, e.reads, e.writes, e.errors = r.requests, r.reads, r.writes, r.errors
            e.errors_4xx, e.errors_5xx, e.auth_denied = r.errors_4xx, r.errors_5xx, r.auth_denied
            e.response_bytes = r.response_bytes
            -- nil 대입은 Lua 에서 no-op 이라, 표본이 없으면 필드 자체가 생기지 않는다.
            e.last_read_bytes  = r.last_read_bytes
            e.last_write_bytes = r.last_write_bytes
            e.commit_count     = r.commit_count
            e.commit_ms_sum    = r.commit_ms_sum
            e.commit_ms_min    = r.commit_ms_min
            e.commit_ms_max    = r.commit_ms_max

            local extra = ""
            if r.last_read_bytes ~= nil or r.last_write_bytes ~= nil then
                extra = string.format(", last read %s, last write %s",
                    r.last_read_bytes  and tostring(r.last_read_bytes)  or "-",
                    r.last_write_bytes and tostring(r.last_write_bytes) or "-")
            end
            if r.commit_count ~= nil then
                -- 평균은 표시용으로만 _msg 에 쓴다. 필드로 저장하지 않는다 — 평균끼리는
                -- 합칠 수 없다. 기간 평균은 항상 sum(commit_ms_sum) / sum(commit_count).
                extra = extra .. string.format(", commits %d (min/avg/max %d/%d/%d ms)",
                    r.commit_count, r.commit_ms_min,
                    math.floor(r.commit_ms_sum / r.commit_count + 0.5), r.commit_ms_max)
            end
            e._msg = string.format(
                "seq=%d resource %s (%s/%s): %d requests, %d reads, %d writes, "
                .. "%d errors (%d 4xx, %d 5xx, %d denied), %d bytes%s",
                report_seq, key, e.api_kind, e.resource_kind, r.requests, r.reads, r.writes,
                r.errors, r.errors_4xx, r.errors_5xx, r.auth_denied, r.response_bytes, extra)
            rows[#rows + 1] = e
            -- distinct_resources 는 "요청 > 0" 인 행만 센다. 커밋만 있는 행은 제외.
            if r.requests > 0 then n_active_res = n_active_res + 1 end
        end
    end

    for user, r in pairs(counts.principals) do
        if r.requests > 0 then
            local e = base("principal")
            e.user_principal_name = user
            e.requests, e.reads, e.writes, e.errors = r.requests, r.reads, r.writes, r.errors
            e.errors_4xx, e.errors_5xx, e.auth_denied = r.errors_4xx, r.errors_5xx, r.auth_denied
            e.response_bytes = r.response_bytes
            e._msg = string.format(
                "seq=%d principal %s: %d requests, %d reads, %d writes, "
                .. "%d errors (%d 4xx, %d 5xx, %d denied), %d bytes",
                report_seq, user, r.requests, r.reads, r.writes,
                r.errors, r.errors_4xx, r.errors_5xx, r.auth_denied, r.response_bytes)
            rows[#rows + 1] = e
            n_active_pri = n_active_pri + 1
        end
    end

    for name, n in pairs(counts.dropped) do
        if n > 0 then
            local e = base("app_dropped")
            e.logger_name = name
            e.dropped     = n
            e._msg = string.format("seq=%d app_dropped %s: %d lines", report_seq, name, n)
            rows[#rows + 1] = e
        end
    end

    s.access_seen         = counts.access_seen
    s.access_kept         = counts.access_seen - counts.access_counted
    s.access_counted      = counts.access_counted
    -- 오류 요청이 강제로 만든 롤 행 수. REPORT_MAX_ROLE_KEYS 와 같으면 상한 도달.
    s.role_keys_forced    = counts.role_keys_forced
    s.counted_read        = counts.counted_read
    s.counted_post        = counts.counted_post
    s.errors_kept         = counts.errors_kept
    s.parse_errors        = counts.parse_errors
    s.errors_4xx          = tot_4xx
    s.errors_5xx          = tot_5xx
    s.auth_denied         = tot_denied
    s.bytes_total         = tot_bytes
    s.distinct_resources  = n_active_res
    s.distinct_principals = n_active_pri
    s.resources_other     = counts.resources_over
    s.resources_other_distinct = counts.n_other_keys
    s.principals_other    = counts.principals_over
    s.app_dropped_total   = counts.dropped_total
    s.counted_404         = counts.counted_404
    s.app_dropped_404     = counts.app_dropped_404
    s.held_orphans        = counts.held_orphans
    s.held_pending        = held_count
    s.windows_skipped     = windows_skipped or 0
    -- 트래픽 없는 윈도우에서는 필드 자체를 생략한다 ("" 금지). 빈 문자열은 새 일별 인덱스의
    -- 동적 매핑을 text 로 굳혀 날짜 쿼리를 영구히 막는다 (polaris-report-2026.09.10 실측).
    -- 인덱스 템플릿이 date 로 선언하므로, "" 는 HTTP 200 인 _bulk 안에서 건별로 거부된다.
    s.min_record_time     = counts.min_time
    s.max_record_time     = counts.max_time
    s.partial_window      = counts.partial and "true" or "false"
    s._msg = string.format(
        "polaris shipper report seq=%d@%s %s..%s: %d access lines, %d kept, "
        .. "%d counted (%d read, %d POST, %d 404), %d errors kept (%d 4xx, %d 5xx, "
        .. "%d denied), %d resources, %d principals, %d app lines dropped, %d bytes, "
        .. "%d windows skipped",
        report_seq, host, starts, ends, counts.access_seen, s.access_kept,
        counts.access_counted, counts.counted_read, counts.counted_post, counts.counted_404,
        counts.errors_kept, tot_4xx, tot_5xx, tot_denied,
        n_active_res, n_active_pri, counts.dropped_total, tot_bytes, s.windows_skipped)

    out[#out + 1] = s
    for _, e in ipairs(rows) do out[#out + 1] = e end
    return out
end

-- 리포트 틱. Interval_Sec 마다 한 번 들어오며, 현재 윈도우 안의 틱은 버린다.
-- 과잉 틱은 무해하고, 부족한 틱은 해롭다: 틱 주기가 윈도우에 가까워지면 지터로 경계 두 개가
-- 틱 사이를 지나가고, 건너뛴 윈도우는 열리지 않은 채 이전 윈도우에 합쳐진다.
--
-- ⚠ 윈도우 라벨 스큐: 경계와 "그 경계를 알아챈 틱" 사이에 들어온 레코드는 방금 닫힌
--   윈도우에 집계된다. 스큐는 틱 위상(0 ~ Interval_Sec)만큼이며, 이 위상은 고정이 아니라
--   천천히 드리프트한다 (같은 파드에서 3.673s → 2.77s, 2026-09-14 → 09-15 실측).
--   경계 기준으로 트래픽을 넣는 테스트는 경계 + Interval_Sec + 1.5s 이후에 시작할 것.
local function report_tick(timestamp, record)
    local idx = math.floor(now_seconds(record) / WINDOW_SECONDS)
    if counts == nil then
        -- 기동 후 첫 틱: 빈 리포트를 내지 않고 윈도우만 연다. 시작 부분을 놓쳤으므로 partial.
        counts = new_window(idx, true)
        return -1, timestamp, record
    end
    if idx == counts.window then
        return -1, timestamp, record
    end
    -- 닫히는 윈도우와 지금 열린 윈도우 사이의 윈도우들은 만들어진 적이 없다. report_seq 는
    -- 간격과 무관하게 1 씩만 오르므로, 그 간격을 windows_skipped 로 명시한다.
    -- 이 클러스터에서는 0 이 아닐 것을 예상하라: OrbStack VM 은 MacBook 과 함께 잠들고,
    -- 그동안 틱은 돌지 않는다. 잠자기는 "큰 windows_skipped + access_seen 0 + min_record_time
    -- 없음", 진짜 틱 실패는 "windows_skipped >= 1 + min/max 폭 > window_seconds" 로 보인다.
    local skipped = idx - counts.window - 1
    if skipped < 0 then skipped = 0 end
    local out = build_report(counts.window, skipped)
    counts = new_window(idx, false)
    return 2, timestamp, out
end


-- ── 진입점 ─────────────────────────────────────────────────────────────────────────────
-- 반환 조립. extra(보류분·고아)가 없으면 원래 코드 그대로, 있으면 레코드 배열로.
local function emit(extra, code, timestamp, record)
    if #extra == 0 then return code, timestamp, record end
    if code ~= -1 then extra[#extra + 1] = record end
    return 2, timestamp, extra
end

function polaris_noise_filter(tag, timestamp, record)
    -- 0. 리포트 틱. 로그 데이터가 없다. 리포트로 치환되거나 버려진다.
    --    (보류분은 여기서 내보내지 않는다: 틱의 반환은 polaris.report 태그로 가서 리포트
    --     인덱스에 들어가기 때문이다. 고아는 다음 polaris.logs 레코드와 함께 나간다.)
    if tag == REPORT_TAG then
        return report_tick(timestamp, record)
    end

    local now = now_seconds(record)
    local extra = {}
    take_orphans(now, extra)

    -- * 적재 여부 판정 전에 가드. 버려질 레코드에 해도 무해하고, 순서 실수를 막는다.
    local changed = redact_secret(record)
    -- 반환 코드: 레코드를 바꿨으면 2, 아니면 0.
    local keep = changed and 2 or 0

    local level = record["level"]

    -- 1. 오류와 경고는 허용 목록과 무관하게 항상, 즉시 남긴다.
    if level == "ERROR" or level == "WARN" then
        return emit(extra, keep, timestamp, record)
    end

    local logger = record["loggerName"]

    -- 2. 애플리케이션 로그 (액세스 로그가 아닌 레코드)
    if logger ~= ACCESS_LOGGER then
        -- 2a. 커밋 시간은 버리기 전에 수확한다.
        if logger == COMMIT_LOGGER then
            count_commit(record["_msg"])
        end
        -- 2b. 허용 목록이면 적재 — 요청 ID 가 있으면 액세스 라인까지 보류.
        if APP_ALLOW[logger] then
            local rid = request_id_of(record)
            if rid == nil then
                return emit(extra, keep, timestamp, record)
            end
            local known = memo[rid]
            if known ~= nil then
                -- 액세스 라인이 이미 지나갔다: 그 상태로 즉시 판정.
                if known.status == 404 then
                    if counts ~= nil then counts.app_dropped_404 = counts.app_dropped_404 + 1 end
                    return emit(extra, -1, timestamp, record)
                end
                return emit(extra, keep, timestamp, record)
            end
            hold(rid, record, now)
            return emit(extra, -1, timestamp, record)
        end
        -- 2c. 그 외는 세고 버린다.
        count_dropped(record)
        return emit(extra, -1, timestamp, record)
    end

    -- 먼저 세고, 나중에 판정한다. 억제될 수 있는 모든 것이 카운터에 들어가야 한다 —
    -- 그렇지 않으면 억제된 레코드는 "요약" 이 아니라 "소실" 이 된다. 이 설계가 막으려는
    -- 단 하나의 실패가 그것이다.
    local method       = record["http_method"]
    local path         = path_only(record["api_path"])
    local user         = record["user_principal_name"] or "-"
    local status       = tonumber(record["http_status"])
    local bytes        = tonumber(record["response_size"]) or 0
    local parse_failed = record["access_log_parse_error"] ~= nil

    count_record(record, method, path, user, status, bytes, parse_failed)

    -- 이 요청의 보류분을 꺼낸다. 액세스 라인의 판정과 운명을 같이한다.
    local rid = request_id_of(record)
    if rid ~= nil then
        if status ~= nil then remember_status(rid, status, now) end
        local pending = release(rid)
        if pending ~= nil then
            if status == 404 and not parse_failed then
                if counts ~= nil then
                    counts.app_dropped_404 = counts.app_dropped_404 + #pending
                end
            else
                for _, r in ipairs(pending) do extra[#extra + 1] = r end
            end
        end
    end

    -- 3'. 404 는 집계만 한다 (errors / errors_4xx 는 count_record 가 이미 셌다).
    if status == 404 and not parse_failed then
        if counts ~= nil then
            counts.counted_404    = counts.counted_404 + 1
            counts.access_counted = counts.access_counted + 1
        end
        return emit(extra, -1, timestamp, record)
    end

    -- 3. 실패한 요청은 전부, 상한 없이 남긴다. 파싱 못 한 라인도 — 읽지 못한 것은 버리지 않는다.
    if parse_failed or status == nil or status >= 400 then
        if counts ~= nil then counts.errors_kept = counts.errors_kept + 1 end
        return emit(extra, keep, timestamp, record)
    end

    -- 4. POST 이외의 변경 요청은 항상 남긴다.
    if KEEP_METHODS[method] then
        return emit(extra, keep, timestamp, record)
    end

    -- 5. POST: management 는 전건 적재, catalog 는 집계만.
    if method == "POST" then
        if path:find(MGMT_PREFIX) then
            return emit(extra, keep, timestamp, record)
        end
        if counts ~= nil then
            counts.counted_post   = counts.counted_post + 1
            counts.access_counted = counts.access_counted + 1
        end
        return emit(extra, -1, timestamp, record)
    end

    -- 6. 성공한 조회는 기록이 아니라 숫자다.
    if READ_METHODS[method] then
        if counts ~= nil then
            counts.counted_read   = counts.counted_read + 1
            counts.access_counted = counts.access_counted + 1
        end
        return emit(extra, -1, timestamp, record)
    end

    -- 7. 그 외는 남긴다.
    return emit(extra, keep, timestamp, record)
end
