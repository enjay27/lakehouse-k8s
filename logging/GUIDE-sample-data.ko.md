# OpenSearch 샘플 데이터 — `polaris-logs-*` (상세) · `polaris-report-*` (요약), 스키마 v6

> 신규 엔지니어 공유용 샘플입니다. 2026-09-16 에 OpenSearch Dev Tools 로 export 한 두 인덱스의 `_source` 에서 레코드를 골라 옮겼습니다.
>
> - **값이 없는 필드는 싣지 않았습니다** (문서에 없는 필드, 빈 문자열, 빈 객체). 보이는 필드가 그 문서에 실제로 저장된 전부입니다.
> - 값은 저장된 타입 그대로입니다 — 숫자는 숫자(`403`, `184`), 불리언은 불리언. (Dashboards CSV export 와 달리 쉼표 포맷·문자열 변환이 없습니다.)
> - `message` 의 줄바꿈은 JSON 규칙에 따라 `\n` 으로 이스케이프했습니다. Dev Tools 응답 패널을 거쳤기 때문에 **여러 줄 `message` 의 들여쓰기 공백은 원본과 다를 수 있습니다** (값의 내용은 같음).
> - `clientSecret` 은 Polaris 가 로그에 이미 `*` 로 마스킹해 남깁니다. 마스킹이 빠진 값이 들어오면 파이프라인이 `<redacted>` 로 바꾸고 `secret_redacted: true` 를 붙입니다.
> - 시간대: `@timestamp` · `_time` 은 UTC (`Z`). KST 는 +9 시간입니다. access log `message` 안의 시간도 UTC(+0000).
> - **스키마 v6 기준** (2026-09-16 적용). 이전 문서의 `_msg`, `app`, `level: REPORT`, `threadName`/`threadId`, `flb_tag`, `stream` 은 더 이상 없습니다.

## 목차

1. [데이터 개요](#1-데이터-개요)
2. [상세 — HTTP Access Log](#2-상세--http-access-log)
3. [상세 — Admin 감사 로그 (PolarisServiceImpl)](#3-상세--admin-감사-로그-polarisserviceimpl)
4. [상세 — Exception Mapper (INFO)](#4-상세--exception-mapper-info)
5. [상세 — ERROR + Stack Trace](#5-상세--error--stack-trace)
6. [상세 — requestId 단위 요청 추적](#6-상세--requestid-단위-요청-추적)
7. [요약 — summary](#7-요약--summary)
8. [요약 — principal](#8-요약--principal)
9. [요약 — resource](#9-요약--resource)
10. [요약 — app_dropped](#10-요약--app_dropped)
11. [검색 쿼리 예시 (DQL)](#11-검색-쿼리-예시-dql)

---

## 1. 데이터 개요

- **상세 `polaris-logs-2026.09.16`** (386건): Polaris Pod `benchmarks-polaris-777c948595-qnbxl` 의 로그 중 **적재 대상만** 남은 문서. 2026-09-16 16:02:07 ~ 2026-09-16 16:02:42 UTC (2026-09-17 01:02 KST 전후).
  - `io.quarkus.http.access-log` 243건 — 요청 1건 = 1줄. 적재되는 것은 404 를 뺀 4xx/5xx, PUT·DELETE·PATCH, management POST 뿐
  - `org.apache.polaris.service.exception.IcebergExceptionMapper` 78건 — 예외 → HTTP 응답 변환 (`INFO` 74 / `ERROR` 4)
  - `org.apache.polaris.service.admin.PolarisServiceImpl` 65건 — 관리 API 동작 기록 (생성·grant·assign)
- **요약 `polaris-report-2026.09.16`** (67건): Fluent Bit Pod `benchmarks-fluent-bit-62klp` 가 윈도우 `2026-09-16T16:02:30Z` ~ `2026-09-16T16:03:00Z` (30초, 검증용 길이; 운영은 30분) 를 닫으며 만든 행.
  - `report_type`: `summary` 1 / `principal` 4 / `resource` 57 / `app_dropped` 5
- export 구간은 요약 윈도우보다 넓습니다: 상세 386건 중 윈도우 안(`_time` 기준)의 문서는 300건 (access 200 / PolarisServiceImpl 22 / IcebergExceptionMapper 78) 이고, 나머지는 노트북 준비 단계(직전 윈도우)의 문서입니다.
- **적재되지 않은 것은 요약에 숫자로 남습니다.** 이 윈도우의 access log 는 355줄이었고, 그중 200줄만 상세 인덱스에 있습니다. 나머지 155줄(성공한 조회 31, catalog POST 24, **404 100**)은 `summary`·`resource`·`principal` 행의 카운터로만 존재합니다. 허용 목록 밖 애플리케이션 로그 155줄은 `app_dropped` 행에, 404 요청에 딸린 로그 110줄은 `summary.app_dropped_404` 에 있습니다.
- 권한 매트릭스 테스트 노트북(`nb-1789574527-*`, `mx_1789574527_*`)이 일부러 에러를 유발한 실행이라 에러 비율이 운영보다 높습니다.
- 같은 요청의 로그는 `mdc.requestId` 로, 같은 집계 윈도우의 요약 행은 `window_start` + `hostname` (또는 `report_seq` + `hostname`) 으로 묶입니다.

---

## 2. 상세 — HTTP Access Log

`message` 는 Quarkus 액세스 로그 원문이고, 파이프라인이 그것을 `client_ip` · `user_principal_name` · `http_method` · `api_path` · `http_status` · `response_size` 로 분해합니다. `user_principal_name: "-"` 는 결측이 아니라 **미인증/인증 실패**입니다.

#### 2.1 200 OK — PUT (카탈로그 수정)

```json
{
  "@timestamp": "2026-09-16T16:02:37.394Z",
  "_time": "2026-09-16T16:02:37.394090652Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [16/Sep/2026:16:02:37 +0000] \"PUT /api/management/v1/catalogs/mx1789574527cat2 HTTP/1.1\" 200 523",
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "PUT",
  "api_path": "/api/management/v1/catalogs/mx1789574527cat2",
  "http_status": 200,
  "response_size": 523,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2035-updateCatalog-2",
    "realmId": "POLARIS"
  },
  "sequence": 43971
}
```

#### 2.2 200 OK — POST (자격증명 reset)

```json
{
  "@timestamp": "2026-09-16T16:02:37.861Z",
  "_time": "2026-09-16T16:02:37.861689736Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [16/Sep/2026:16:02:37 +0000] \"POST /api/management/v1/principals/mx_1789574527_p2/reset HTTP/1.1\" 200 294",
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/management/v1/principals/mx_1789574527_p2/reset",
  "http_status": 200,
  "response_size": 294,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2062-resetCredentials-2",
    "realmId": "POLARIS"
  },
  "sequence": 44314
}
```

#### 2.3 201 Created — POST (카탈로그 생성)

```json
{
  "@timestamp": "2026-09-16T16:02:07.988Z",
  "_time": "2026-09-16T16:02:07.9887276Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [16/Sep/2026:16:02:07 +0000] \"POST /api/management/v1/catalogs HTTP/1.1\" 201 519",
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/management/v1/catalogs",
  "http_status": 201,
  "response_size": 519,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000890",
    "realmId": "POLARIS"
  },
  "sequence": 42043
}
```

#### 2.4 201 Created — PUT (catalog-role grant 추가)

```json
{
  "@timestamp": "2026-09-16T16:02:08.473Z",
  "_time": "2026-09-16T16:02:08.473601295Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [16/Sep/2026:16:02:08 +0000] \"PUT /api/management/v1/catalogs/apimatrix1789574527_cat/catalog-roles/catalog_admin/grants HTTP/1.1\" 201 -",
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "PUT",
  "api_path": "/api/management/v1/catalogs/apimatrix1789574527_cat/catalog-roles/catalog_admin/grants",
  "http_status": 201,
  "response_size": 0,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000894",
    "realmId": "POLARIS"
  },
  "sequence": 42094
}
```

#### 2.5 204 No Content — DELETE (테이블 삭제)

```json
{
  "@timestamp": "2026-09-16T16:02:36.740Z",
  "_time": "2026-09-16T16:02:36.740289237Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789574527_runner [16/Sep/2026:16:02:36 +0000] \"DELETE /api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns/tables/mx_1789574527_tbl_doomed HTTP/1.1\" 204 -",
  "user_principal_name": "mx_1789574527_runner",
  "client_ip": "192.168.194.1",
  "http_method": "DELETE",
  "api_path": "/api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns/tables/mx_1789574527_tbl_doomed",
  "http_status": 204,
  "response_size": 0,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2012-dropTable-2",
    "realmId": "POLARIS"
  },
  "sequence": 43555
}
```

#### 2.6 400 Bad Request — POST (테이블 등록, 잘못된 본문)

```json
{
  "@timestamp": "2026-09-16T16:02:36.676Z",
  "_time": "2026-09-16T16:02:36.67614848Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789574527_runner [16/Sep/2026:16:02:36 +0000] \"POST /api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns/register HTTP/1.1\" 400 171",
  "user_principal_name": "mx_1789574527_runner",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns/register",
  "http_status": 400,
  "response_size": 171,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2009-registerTable-2",
    "realmId": "POLARIS"
  },
  "sequence": 43466
}
```

#### 2.7 400 Bad Request — DELETE (비어있지 않은 카탈로그 삭제)

```json
{
  "@timestamp": "2026-09-16T16:02:40.674Z",
  "_time": "2026-09-16T16:02:40.673933893Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [16/Sep/2026:16:02:40 +0000] \"DELETE /api/management/v1/catalogs/nb1789574527bh HTTP/1.1\" 400 123",
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "DELETE",
  "api_path": "/api/management/v1/catalogs/nb1789574527bh",
  "http_status": 400,
  "response_size": 123,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000970",
    "realmId": "POLARIS"
  },
  "sequence": 46580
}
```

#### 2.8 401 Unauthorized — GET, 쿼리스트링 포함 (토큰 없음)

```json
{
  "@timestamp": "2026-09-16T16:02:37.923Z",
  "_time": "2026-09-16T16:02:37.92296519Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - - [16/Sep/2026:16:02:37 +0000] \"GET /api/catalog/v1/config?warehouse=apimatrix1789574527_cat HTTP/1.1\" 401 -",
  "user_principal_name": "-",
  "client_ip": "192.168.194.1",
  "http_method": "GET",
  "api_path": "/api/catalog/v1/config?warehouse=apimatrix1789574527_cat",
  "http_status": 401,
  "response_size": 0,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2064-getConfig-401",
    "realmId": "POLARIS"
  },
  "sequence": 44325
}
```

#### 2.9 401 Unauthorized — POST (OAuth 토큰)

```json
{
  "@timestamp": "2026-09-16T16:02:37.940Z",
  "_time": "2026-09-16T16:02:37.940356385Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - - [16/Sep/2026:16:02:37 +0000] \"POST /api/catalog/v1/oauth/tokens HTTP/1.1\" 401 99",
  "user_principal_name": "-",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/oauth/tokens",
  "http_status": 401,
  "response_size": 99,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2066-getToken-401",
    "realmId": "POLARIS"
  },
  "sequence": 44346
}
```

#### 2.10 403 Forbidden — GET (권한 없는 principal)

```json
{
  "@timestamp": "2026-09-16T16:02:37.960Z",
  "_time": "2026-09-16T16:02:37.960307965Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789574527_denied [16/Sep/2026:16:02:37 +0000] \"GET /api/catalog/v1/apimatrix1789574527_cat/namespaces HTTP/1.1\" 403 251",
  "user_principal_name": "mx_1789574527_denied",
  "client_ip": "192.168.194.1",
  "http_method": "GET",
  "api_path": "/api/catalog/v1/apimatrix1789574527_cat/namespaces",
  "http_status": 403,
  "response_size": 251,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2068-listNamespaces-403",
    "realmId": "POLARIS"
  },
  "sequence": 44358
}
```

#### 2.11 403 Forbidden — POST (자격증명 rotate 거부)

```json
{
  "@timestamp": "2026-09-16T16:02:37.887Z",
  "_time": "2026-09-16T16:02:37.887688465Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [16/Sep/2026:16:02:37 +0000] \"POST /api/management/v1/principals/mx_1789574527_p2/rotate HTTP/1.1\" 403 214",
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/management/v1/principals/mx_1789574527_p2/rotate",
  "http_status": 403,
  "response_size": 214,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2063-rotateCredentials-2",
    "realmId": "POLARIS"
  },
  "sequence": 44323
}
```

#### 2.12 403 Forbidden — HEAD (존재 확인 거부)

```json
{
  "@timestamp": "2026-09-16T16:02:38.154Z",
  "_time": "2026-09-16T16:02:38.154039826Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789574527_denied [16/Sep/2026:16:02:38 +0000] \"HEAD /api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns/tables/probe_tbl HTTP/1.1\" 403 -",
  "user_principal_name": "mx_1789574527_denied",
  "client_ip": "192.168.194.1",
  "http_method": "HEAD",
  "api_path": "/api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns/tables/probe_tbl",
  "http_status": 403,
  "response_size": 0,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2101-tableExists-403",
    "realmId": "POLARIS"
  },
  "sequence": 44630
}
```

#### 2.13 409 Conflict — PUT (stale entity version)

```json
{
  "@timestamp": "2026-09-16T16:02:39.062Z",
  "_time": "2026-09-16T16:02:39.06245247Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [16/Sep/2026:16:02:39 +0000] \"PUT /api/management/v1/catalogs/mx1789574527cat2 HTTP/1.1\" 409 134",
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "PUT",
  "api_path": "/api/management/v1/catalogs/mx1789574527cat2",
  "http_status": 409,
  "response_size": 134,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2271-updateCatalog-409",
    "realmId": "POLARIS"
  },
  "sequence": 46046
}
```

#### 2.14 409 Conflict — POST (이미 존재하는 카탈로그 생성)

```json
{
  "@timestamp": "2026-09-16T16:02:39.051Z",
  "_time": "2026-09-16T16:02:39.051594093Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [16/Sep/2026:16:02:39 +0000] \"POST /api/management/v1/catalogs HTTP/1.1\" 409 150",
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/management/v1/catalogs",
  "http_status": 409,
  "response_size": 150,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2269-createCatalog-409",
    "realmId": "POLARIS"
  },
  "sequence": 46031
}
```

#### 2.15 422 Unprocessable — POST (스토리지 연결 실패, 테이블 생성)

```json
{
  "@timestamp": "2026-09-16T16:02:39.876Z",
  "_time": "2026-09-16T16:02:39.876600736Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789574527_runner [16/Sep/2026:16:02:39 +0000] \"POST /api/catalog/v1/nb1789574527bh/namespaces/bh_ns/tables HTTP/1.1\" 422 227",
  "user_principal_name": "mx_1789574527_runner",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/nb1789574527bh/namespaces/bh_ns/tables",
  "http_status": 422,
  "response_size": 227,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-3201-probe-500-black_hole_endpoint-create_table_0",
    "realmId": "POLARIS"
  },
  "sequence": 46497
}
```

#### 2.16 500 Internal Server Error — POST (table rename)

```json
{
  "@timestamp": "2026-09-16T16:02:39.000Z",
  "_time": "2026-09-16T16:02:39.00016997Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789574527_runner [16/Sep/2026:16:02:39 +0000] \"POST /api/catalog/v1/apimatrix1789574527_cat/tables/rename HTTP/1.1\" 500 168",
  "user_principal_name": "mx_1789574527_runner",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/apimatrix1789574527_cat/tables/rename",
  "http_status": 500,
  "response_size": 168,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2264-renameTable-400",
    "realmId": "POLARIS"
  },
  "sequence": 45951
}
```

> **404 는 상세 인덱스에 없습니다** (정책 v5). 404 요청은 `summary.counted_404` 와 `resource` / `principal` 행의 `errors_4xx` 에 숫자로만 남고, 같은 `requestId` 의 예외·서비스 로그도 함께 버려집니다 (`summary.app_dropped_404`). 원본 줄이 필요하면 공용 인덱스 `k8s-logs-*` (5일) 를 봅니다.

---

## 3. 상세 — Admin 감사 로그 (PolarisServiceImpl)

관리 API 가 **무엇을 바꿨는지** 남기는 로그입니다. 요청의 결과(성공/거부)는 같은 `mdc.requestId` 의 access log 로 확인합니다 — 거부된 요청도 "시도" 로그는 먼저 찍힙니다.

#### 3.1 Created — catalog (→ 201)

```json
{
  "@timestamp": "2026-09-16T16:02:07.988Z",
  "_time": "2026-09-16T16:02:07.987150635Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Created new catalog class PolarisCatalog {\n    class Catalog {\n        type: INTERNAL\n        name: apimatrix1789574527_cat\n        properties: class CatalogProperties {\n            {polaris.config.drop-with-purge.enabled=true, default-base-location=s3a://data-catalog-bucket/apimatrix1789574527_cat/}\n            defaultBaseLocation: s3a://data-catalog-bucket/apimatrix1789574527_cat/\n        }\n        createTimestamp: 1789574527960\n        lastUpdateTimestamp: 0\n        entityVersion: 1\n        storageConfigInfo: class AwsStorageConfigInfo {\n            class StorageConfigInfo {\n                storageType: S3\n                allowedLocations: [s3a://data-catalog-bucket/apimatrix1789574527_cat/, s3a://data-catalog-bucket/]\n            }\n            roleArn: null\n            externalId: null\n            userArn: null\n            region: null\n            endpoint: http://192.168.139.2:9000\n            stsEndpoint: null\n            stsUnavailable: null\n            endpointInternal: http://192.168.139.2:9000\n            pathStyleAccess: true\n        }\n    }\n}",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000890",
    "realmId": "POLARIS"
  },
  "sequence": 42042
}
```

#### 3.2 Created — principal (clientSecret 마스킹) (→ 201)

```json
{
  "@timestamp": "2026-09-16T16:02:07.831Z",
  "_time": "2026-09-16T16:02:07.830514507Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Created new principal class PrincipalWithCredentials {\n    principal: class Principal {\n        name: mx_1789574527_denied\n        clientId: 7b47b5730213bcde\n        properties: {}\n        createTimestamp: 1789574527815\n        lastUpdateTimestamp: 0\n        entityVersion: 1\n    }\n    credentials: class PrincipalWithCredentialsCredentials {\n        clientId: 7b47b5730213bcde\n        clientSecret: *\n    }\n}",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000884",
    "realmId": "POLARIS"
  },
  "sequence": 41951
}
```

#### 3.3 Created — principalRole (→ 201)

```json
{
  "@timestamp": "2026-09-16T16:02:07.847Z",
  "_time": "2026-09-16T16:02:07.846710697Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Created new principalRole class PrincipalRole {\n    name: mx_1789574527_denied_role\n    federated: false\n    properties: {}\n    createTimestamp: 1789574527843\n    lastUpdateTimestamp: 1789574527843\n    entityVersion: 1\n}",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000885",
    "realmId": "POLARIS"
  },
  "sequence": 41961
}
```

#### 3.4 Created — catalogRole (→ 201)

```json
{
  "@timestamp": "2026-09-16T16:02:08.679Z",
  "_time": "2026-09-16T16:02:08.679733622Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Created new catalogRole class CatalogRole {\n    name: apimatrix1789574527_shared\n    properties: {}\n    createTimestamp: 1789574528677\n    lastUpdateTimestamp: 1789574528677\n    entityVersion: 1\n}",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000902",
    "realmId": "POLARIS"
  },
  "sequence": 42274
}
```

#### 3.5 Adding grant — catalog-role 에 privilege 부여 (→ 201)

```json
{
  "@timestamp": "2026-09-16T16:02:08.473Z",
  "_time": "2026-09-16T16:02:08.459435571Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Adding grant class AddGrantRequest {\n    grant: class CatalogGrant {\n        class GrantResource {\n            type: catalog\n        }\n        privilege: CATALOG_MANAGE_CONTENT\n    }\n} to catalogRole catalog_admin in catalog apimatrix1789574527_cat",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000894",
    "realmId": "POLARIS"
  },
  "sequence": 42087
}
```

#### 3.6 Revoking grant (→ 400)

```json
{
  "@timestamp": "2026-09-16T16:02:37.569Z",
  "_time": "2026-09-16T16:02:37.568108433Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Revoking grant class RevokeGrantRequest {\n    grant: class CatalogGrant {\n        class GrantResource {\n            type: catalog\n        }\n        privilege: CATALOG_MANAGE_ACCESS\n    }\n} from catalogRole mx_1789574527_crole in catalog apimatrix1789574527_cat",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2042-revokeGrantFromCatalogRole-2",
    "realmId": "POLARIS"
  },
  "sequence": 44050
}
```

#### 3.7 Assigning principalRole → principal (→ 201)

```json
{
  "@timestamp": "2026-09-16T16:02:07.879Z",
  "_time": "2026-09-16T16:02:07.858928954Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Assigning principalRole mx_1789574527_denied_role to principal mx_1789574527_denied",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000886",
    "realmId": "POLARIS"
  },
  "sequence": 41969
}
```

#### 3.8 Assigning catalogRole → principalRole (→ 201)

```json
{
  "@timestamp": "2026-09-16T16:02:09.441Z",
  "_time": "2026-09-16T16:02:09.426124533Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Assigning catalogRole apimatrix1789574527_shared in catalog apimatrix1789574527_cat to principalRole mx_1789574527_runner_role",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000953",
    "realmId": "POLARIS"
  },
  "sequence": 43029
}
```

---

## 4. 상세 — Exception Mapper (INFO)

access log 가 **무엇이** 실패했는지 보여준다면, 이 로그는 **왜** 실패했는지 보여줍니다. 대부분 access log 보다 몇 ms 먼저 찍힙니다.

#### 4.1 권한 거부 — 권한 없는 principal (→ 403)

```json
{
  "@timestamp": "2026-09-16T16:02:37.960Z",
  "_time": "2026-09-16T16:02:37.959325878Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Principal 'mx_1789574527_denied' with activated PrincipalRoles '[mx_1789574527_denied_role]' and activated grants via '[mx_1789574527_denied_role]' is not authorized for op LIST_NAMESPACES",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2068-listNamespaces-403",
    "realmId": "POLARIS"
  },
  "sequence": 44357
}
```

#### 4.2 root 도 권한 거부 (→ 403)

```json
{
  "@timestamp": "2026-09-16T16:02:37.887Z",
  "_time": "2026-09-16T16:02:37.887551465Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Principal 'root' with activated PrincipalRoles '[service_admin]' and activated grants via '[service_admin]' is not authorized for op ROTATE_CREDENTIALS",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2063-rotateCredentials-2",
    "realmId": "POLARIS"
  },
  "sequence": 44322
}
```

#### 4.3 Only Root principal 전용 작업 (→ 403)

```json
{
  "@timestamp": "2026-09-16T16:02:38.752Z",
  "_time": "2026-09-16T16:02:38.751954474Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Only Root principal(service-admin) can perform RESET_CREDENTIALS",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2239-resetCredentials-403",
    "realmId": "POLARIS"
  },
  "sequence": 45583
}
```

#### 4.4 이미 존재 (→ 409)

```json
{
  "@timestamp": "2026-09-16T16:02:39.051Z",
  "_time": "2026-09-16T16:02:39.051440426Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Cannot create Catalog mx1789574527cat2. Catalog already exists or resolution failed",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2269-createCatalog-409",
    "realmId": "POLARIS"
  },
  "sequence": 46030
}
```

#### 4.5 비어있지 않은 카탈로그 삭제 (→ 400)

```json
{
  "@timestamp": "2026-09-16T16:02:40.674Z",
  "_time": "2026-09-16T16:02:40.673511808Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Catalog 'nb1789574527bh' cannot be dropped, it is not empty",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "8d603ae8-3762-467a-a6b5-64afdd41db5b_0000000000000000970",
    "realmId": "POLARIS"
  },
  "sequence": 46579
}
```

#### 4.6 요청 본문 파싱 실패 (→ 400)

```json
{
  "@timestamp": "2026-09-16T16:02:38.855Z",
  "_time": "2026-09-16T16:02:38.855634724Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Cannot parse missing string: name",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2251-registerTable-400",
    "realmId": "POLARIS"
  },
  "sequence": 45713
}
```

#### 4.7 warehouse 미지정 (→ 400)

```json
{
  "@timestamp": "2026-09-16T16:02:38.800Z",
  "_time": "2026-09-16T16:02:38.800371044Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Please specify a warehouse",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2244-getConfig-400",
    "realmId": "POLARIS"
  },
  "sequence": 45624
}
```

#### 4.8 스토리지 자격증명 발급 실패 — 연결 거부 (endpoint 127.0.0.1:1) (→ 422)

```json
{
  "@timestamp": "2026-09-16T16:02:39.876Z",
  "_time": "2026-09-16T16:02:39.875590232Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Failed to get subscoped credentials: Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused (SDK Attempt Count: 4)",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-3201-probe-500-black_hole_endpoint-create_table_0",
    "realmId": "POLARIS"
  },
  "sequence": 46496
}
```

#### 4.9 스토리지 자격증명 발급 실패 — 호스트 해석 불가 (UnknownHostException) (→ 422)

```json
{
  "@timestamp": "2026-09-16T16:02:41.354Z",
  "_time": "2026-09-16T16:02:41.353874496Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Failed to get subscoped credentials: Received an UnknownHostException when attempting to interact with a service. See cause for the exact endpoint that is failing to resolve. If this is happening on an endpoint that previously worked, there may be a network connectivity issue or your DNS cache could be storing endpoints for too long.",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-3204-probe-500-unresolvable_host-create_table_0",
    "realmId": "POLARIS"
  },
  "sequence": 46674
}
```

#### 4.10 버킷 없음 (→ 400)

```json
{
  "@timestamp": "2026-09-16T16:02:42.024Z",
  "_time": "2026-09-16T16:02:42.023936393Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException The specified bucket does not exist (Service: S3, Status Code: 404, Request ID: 18D5D8952409C0C5, Extended Request ID: dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8) (SDK Attempt Count: 1)",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-3207-probe-500-nonexistent_bucket-create_table_0",
    "realmId": "POLARIS"
  },
  "sequence": 46862
}
```

---

## 5. 상세 — ERROR + Stack Trace

> `exception` 은 객체로 저장됩니다: `exceptionType`, `message`, `refId`, 그리고 프레임 배열 `frames` (`class` / `method` / `line`). line 정보가 없는 프레임은 `line` 키가 없습니다. 아래는 저장된 순서 그대로입니다 (맨 위가 예외 발생 지점).

#### 5.1 NullPointerException — OAuth 토큰

```json
{
  "@timestamp": "2026-09-16T16:02:38.804Z",
  "_time": "2026-09-16T16:02:38.804258976Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2245-getToken-400",
    "realmId": "POLARIS"
  },
  "sequence": 45629,
  "exception": {
    "refId": 1,
    "exceptionType": "java.lang.NullPointerException",
    "message": "Cannot invoke \"Object.equals(Object)\" because \"o\" is null",
    "frames": [
      {"class": "java.util.ImmutableCollections$Set12", "method": "contains", "line": 817},
      {"class": "org.apache.polaris.service.auth.internal.broker.JWTBroker", "method": "supportsGrantType", "line": 169},
      {"class": "org.apache.polaris.service.auth.internal.broker.ServiceProducers_ProducerMethod_tokenBroker_pKyuSLrp6V1EV14KaXDBTA1e90o_ClientProxy", "method": "supportsGrantType"},
      {"class": "org.apache.polaris.service.auth.internal.service.DefaultOAuth2ApiService", "method": "getToken", "line": 72},
      {"class": "org.apache.polaris.service.auth.internal.service.DefaultOAuth2ApiService_ClientProxy", "method": "getToken"},
      {"class": "org.apache.polaris.service.catalog.api.ServiceProducers_ProducerMethod_icebergRestOAuth2ApiService_MtUuMFyhMWQ9p67dec6El1hvgiM_ClientProxy", "method": "getToken"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api", "method": "getToken", "line": 99},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api_Subclass", "method": "getToken$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api_Subclass$$function$$1", "method": "apply"},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 73},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$8", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.Future", "method": "from", "line": 85},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$9", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.FaultToleranceContext", "method": "call", "line": 20},
      {"class": "io.smallrye.faulttolerance.core.Invocation", "method": "apply", "line": 29},
      {"class": "io.smallrye.faulttolerance.core.metrics.MetricsCollector", "method": "apply", "line": 98},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "syncFlow", "line": 367},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "intercept", "line": 205},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor", "method": "timedMethod", "line": 79},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
      {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api_Subclass", "method": "getToken"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api$quarkusrestinvoker$getToken_f6dd65d68bbb7be8bc087c1c82d2d2a56984933f", "method": "invoke"},
      {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 183},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 645},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ]
  }
}
```

#### 5.2 NullPointerException — namespace 생성

```json
{
  "@timestamp": "2026-09-16T16:02:38.824Z",
  "_time": "2026-09-16T16:02:38.823826346Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2247-createNamespace-400",
    "realmId": "POLARIS"
  },
  "sequence": 45660,
  "exception": {
    "refId": 1,
    "exceptionType": "java.lang.NullPointerException",
    "message": "Cannot invoke \"org.apache.iceberg.catalog.Namespace.isEmpty()\" because \"namespace\" is null",
    "frames": [
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "createNamespace", "line": 284},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$createNamespace$0", "line": 239},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 199},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "createNamespace", "line": 236},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createNamespace$$superforward"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "createNamespace"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "createNamespace", "line": 117},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createNamespace"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "createNamespace"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "createNamespace", "line": 154},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createNamespace$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$$function$$2", "method": "apply"},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 73},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$8", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.Future", "method": "from", "line": 85},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$9", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.FaultToleranceContext", "method": "call", "line": 20},
      {"class": "io.smallrye.faulttolerance.core.Invocation", "method": "apply", "line": 29},
      {"class": "io.smallrye.faulttolerance.core.metrics.MetricsCollector", "method": "apply", "line": 98},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "syncFlow", "line": 367},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "intercept", "line": 205},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor", "method": "timedMethod", "line": 79},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.quarkus.security.runtime.interceptor.SecurityHandler", "method": "handle", "line": 27},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 29},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 44},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor_RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
      {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createNamespace"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$createNamespace_c8574a4d4e1460a5c4e7917c1b4a8f9a89ead5e4", "method": "invoke"},
      {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 183},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 645},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ]
  }
}
```

#### 5.3 NullPointerException — table rename

```json
{
  "@timestamp": "2026-09-16T16:02:39.000Z",
  "_time": "2026-09-16T16:02:38.999934803Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2264-renameTable-400",
    "realmId": "POLARIS"
  },
  "sequence": 45950,
  "exception": {
    "refId": 1,
    "exceptionType": "java.lang.NullPointerException",
    "message": "Cannot invoke \"org.apache.iceberg.catalog.TableIdentifier.namespace()\" because \"identifier\" is null",
    "frames": [
      {"class": "org.apache.polaris.core.catalog.PolarisCatalogHelpers", "method": "tableIdentifierToList", "line": 38},
      {"class": "org.apache.polaris.service.catalog.common.CatalogHandler", "method": "authorizeRenameTableLikeOperationOrThrow", "line": 339},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "renameTable", "line": 956},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$renameTable$12", "line": 527},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 199},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "renameTable", "line": 523},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "renameTable$$superforward"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "renameTable"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "renameTable", "line": 351},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "renameTable"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "renameTable"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "renameTable", "line": 710},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "renameTable$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$$function$$17", "method": "apply"},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 73},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$8", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.Future", "method": "from", "line": 85},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$9", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.FaultToleranceContext", "method": "call", "line": 20},
      {"class": "io.smallrye.faulttolerance.core.Invocation", "method": "apply", "line": 29},
      {"class": "io.smallrye.faulttolerance.core.metrics.MetricsCollector", "method": "apply", "line": 98},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "syncFlow", "line": 367},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "intercept", "line": 205},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor", "method": "timedMethod", "line": 79},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.quarkus.security.runtime.interceptor.SecurityHandler", "method": "handle", "line": 27},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 29},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 44},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor_RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
      {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "renameTable"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$renameTable_c3539e656e4d0d407236da26060fdfabb8d0a0d7", "method": "invoke"},
      {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 183},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 645},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ]
  }
}
```

#### 5.4 NullPointerException — view rename

```json
{
  "@timestamp": "2026-09-16T16:02:39.043Z",
  "_time": "2026-09-16T16:02:39.043899771Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2268-renameView-400",
    "realmId": "POLARIS"
  },
  "sequence": 46018,
  "exception": {
    "refId": 1,
    "exceptionType": "java.lang.NullPointerException",
    "message": "Cannot invoke \"org.apache.iceberg.catalog.TableIdentifier.namespace()\" because \"identifier\" is null",
    "frames": [
      {"class": "org.apache.polaris.core.catalog.PolarisCatalogHelpers", "method": "tableIdentifierToList", "line": 38},
      {"class": "org.apache.polaris.service.catalog.common.CatalogHandler", "method": "authorizeRenameTableLikeOperationOrThrow", "line": 339},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "renameView", "line": 1135},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$renameView$21", "line": 687},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 199},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "renameView", "line": 683},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "renameView$$superforward"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "renameView"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "renameView", "line": 497},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "renameView"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "renameView"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "renameView", "line": 747},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "renameView$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$$function$$18", "method": "apply"},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 73},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$8", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.Future", "method": "from", "line": 85},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$9", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.FaultToleranceContext", "method": "call", "line": 20},
      {"class": "io.smallrye.faulttolerance.core.Invocation", "method": "apply", "line": 29},
      {"class": "io.smallrye.faulttolerance.core.metrics.MetricsCollector", "method": "apply", "line": 98},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "syncFlow", "line": 367},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "intercept", "line": 205},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor", "method": "timedMethod", "line": 79},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.quarkus.security.runtime.interceptor.SecurityHandler", "method": "handle", "line": 27},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 29},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 44},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor_RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
      {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "renameView"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$renameView_a013d1f5d550ba5989aff78202fe5868b5f128cc", "method": "invoke"},
      {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 183},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 645},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ]
  }
}
```

---

## 6. 상세 — requestId 단위 요청 추적

같은 `mdc.requestId` 를 가진 문서 전체를 **시간순**(`_time`)으로 나열했습니다. 순서 패턴: (서비스 로그) → (예외 처리) → (access log). Dashboards 기본 정렬은 최신순이라 화면에서는 반대로 보입니다.

> 한 요청의 문서들은 파이프라인에서 함께 판정되므로 `@timestamp` 가 access log 시각으로 같아질 수 있습니다. 원래 시각은 `_time` 입니다.

#### 6.1 500 에러 — view rename (3줄)

requestId 끝의 `-400` 은 테스트가 기대한 상태, 실제 응답은 500.

```json
{
  "@timestamp": "2026-09-16T16:02:39.044Z",
  "_time": "2026-09-16T16:02:39.043852645Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Cannot invoke \"org.apache.iceberg.catalog.TableIdentifier.namespace()\" because \"identifier\" is null",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2268-renameView-400",
    "realmId": "POLARIS"
  },
  "sequence": 46017
}
```

```json
{
  "@timestamp": "2026-09-16T16:02:39.043Z",
  "_time": "2026-09-16T16:02:39.043899771Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2268-renameView-400",
    "realmId": "POLARIS"
  },
  "sequence": 46018,
  "exception": {
    "refId": 1,
    "exceptionType": "java.lang.NullPointerException",
    "message": "Cannot invoke \"org.apache.iceberg.catalog.TableIdentifier.namespace()\" because \"identifier\" is null",
    "frames": [
      {"class": "org.apache.polaris.core.catalog.PolarisCatalogHelpers", "method": "tableIdentifierToList", "line": 38},
      {"class": "org.apache.polaris.service.catalog.common.CatalogHandler", "method": "authorizeRenameTableLikeOperationOrThrow", "line": 339},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "renameView", "line": 1135},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$renameView$21", "line": 687},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 199},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "renameView", "line": 683},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "renameView$$superforward"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "renameView"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "renameView", "line": 497},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "renameView"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "renameView"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "renameView", "line": 747},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "renameView$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$$function$$18", "method": "apply"},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 73},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$8", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.Future", "method": "from", "line": 85},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$9", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.FaultToleranceContext", "method": "call", "line": 20},
      {"class": "io.smallrye.faulttolerance.core.Invocation", "method": "apply", "line": 29},
      {"class": "io.smallrye.faulttolerance.core.metrics.MetricsCollector", "method": "apply", "line": 98},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "syncFlow", "line": 367},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "intercept", "line": 205},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor", "method": "timedMethod", "line": 79},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.quarkus.security.runtime.interceptor.SecurityHandler", "method": "handle", "line": 27},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 29},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 44},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor_RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
      {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "renameView"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$renameView_a013d1f5d550ba5989aff78202fe5868b5f128cc", "method": "invoke"},
      {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 183},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 645},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ]
  }
}
```

```json
{
  "@timestamp": "2026-09-16T16:02:39.044Z",
  "_time": "2026-09-16T16:02:39.04406448Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789574527_runner [16/Sep/2026:16:02:39 +0000] \"POST /api/catalog/v1/apimatrix1789574527_cat/views/rename HTTP/1.1\" 500 168",
  "user_principal_name": "mx_1789574527_runner",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/apimatrix1789574527_cat/views/rename",
  "http_status": 500,
  "response_size": 168,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2268-renameView-400",
    "realmId": "POLARIS"
  },
  "sequence": 46019
}
```

#### 6.2 500 에러 — 미인증 OAuth 토큰 요청 (3줄)

```json
{
  "@timestamp": "2026-09-16T16:02:38.804Z",
  "_time": "2026-09-16T16:02:38.804192392Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Cannot invoke \"Object.equals(Object)\" because \"o\" is null",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2245-getToken-400",
    "realmId": "POLARIS"
  },
  "sequence": 45628
}
```

```json
{
  "@timestamp": "2026-09-16T16:02:38.804Z",
  "_time": "2026-09-16T16:02:38.804258976Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2245-getToken-400",
    "realmId": "POLARIS"
  },
  "sequence": 45629,
  "exception": {
    "refId": 1,
    "exceptionType": "java.lang.NullPointerException",
    "message": "Cannot invoke \"Object.equals(Object)\" because \"o\" is null",
    "frames": [
      {"class": "java.util.ImmutableCollections$Set12", "method": "contains", "line": 817},
      {"class": "org.apache.polaris.service.auth.internal.broker.JWTBroker", "method": "supportsGrantType", "line": 169},
      {"class": "org.apache.polaris.service.auth.internal.broker.ServiceProducers_ProducerMethod_tokenBroker_pKyuSLrp6V1EV14KaXDBTA1e90o_ClientProxy", "method": "supportsGrantType"},
      {"class": "org.apache.polaris.service.auth.internal.service.DefaultOAuth2ApiService", "method": "getToken", "line": 72},
      {"class": "org.apache.polaris.service.auth.internal.service.DefaultOAuth2ApiService_ClientProxy", "method": "getToken"},
      {"class": "org.apache.polaris.service.catalog.api.ServiceProducers_ProducerMethod_icebergRestOAuth2ApiService_MtUuMFyhMWQ9p67dec6El1hvgiM_ClientProxy", "method": "getToken"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api", "method": "getToken", "line": 99},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api_Subclass", "method": "getToken$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api_Subclass$$function$$1", "method": "apply"},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 73},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext$NextAroundInvokeInvocationContext", "method": "proceed", "line": 97},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$8", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.Future", "method": "from", "line": 85},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "lambda$syncFlow$9", "line": 364},
      {"class": "io.smallrye.faulttolerance.core.FaultToleranceContext", "method": "call", "line": 20},
      {"class": "io.smallrye.faulttolerance.core.Invocation", "method": "apply", "line": 29},
      {"class": "io.smallrye.faulttolerance.core.metrics.MetricsCollector", "method": "apply", "line": 98},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "syncFlow", "line": 367},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor", "method": "intercept", "line": 205},
      {"class": "io.smallrye.faulttolerance.FaultToleranceInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor", "method": "timedMethod", "line": 79},
      {"class": "io.quarkus.micrometer.runtime.MicrometerTimedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
      {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api_Subclass", "method": "getToken"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api$quarkusrestinvoker$getToken_f6dd65d68bbb7be8bc087c1c82d2d2a56984933f", "method": "invoke"},
      {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 183},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 645},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ]
  }
}
```

```json
{
  "@timestamp": "2026-09-16T16:02:38.804Z",
  "_time": "2026-09-16T16:02:38.804519435Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - - [16/Sep/2026:16:02:38 +0000] \"POST /api/catalog/v1/oauth/tokens HTTP/1.1\" 500 126",
  "user_principal_name": "-",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/oauth/tokens",
  "http_status": 500,
  "response_size": 126,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2245-getToken-400",
    "realmId": "POLARIS"
  },
  "sequence": 45630
}
```

#### 6.3 403 — grant 추가 시도가 거부됨 (3줄)

서비스 로그("Adding grant")는 시도만 기록합니다. 결과는 access log 의 403 입니다.

```json
{
  "@timestamp": "2026-09-16T16:02:38.515Z",
  "_time": "2026-09-16T16:02:38.514884315Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Adding grant class AddGrantRequest {\n    grant: class CatalogGrant {\n        class GrantResource {\n            type: catalog\n        }\n        privilege: CATALOG_MANAGE_ACCESS\n    }\n} to catalogRole mx_1789574527_crole in catalog apimatrix1789574527_cat",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2186-addGrantToCatalogRole-403",
    "realmId": "POLARIS"
  },
  "sequence": 45206
}
```

```json
{
  "@timestamp": "2026-09-16T16:02:38.515Z",
  "_time": "2026-09-16T16:02:38.5154209Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Principal 'mx_1789574527_denied' with activated PrincipalRoles '[mx_1789574527_denied_role]' and activated grants via '[mx_1789574527_denied_role]' is not authorized for op ADD_CATALOG_GRANT_TO_CATALOG_ROLE",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2186-addGrantToCatalogRole-403",
    "realmId": "POLARIS"
  },
  "sequence": 45208
}
```

```json
{
  "@timestamp": "2026-09-16T16:02:38.515Z",
  "_time": "2026-09-16T16:02:38.515567484Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789574527_denied [16/Sep/2026:16:02:38 +0000] \"PUT /api/management/v1/catalogs/apimatrix1789574527_cat/catalog-roles/mx_1789574527_crole/grants HTTP/1.1\" 403 269",
  "user_principal_name": "mx_1789574527_denied",
  "client_ip": "192.168.194.1",
  "http_method": "PUT",
  "api_path": "/api/management/v1/catalogs/apimatrix1789574527_cat/catalog-roles/mx_1789574527_crole/grants",
  "http_status": 403,
  "response_size": 269,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2186-addGrantToCatalogRole-403",
    "realmId": "POLARIS"
  },
  "sequence": 45209
}
```

#### 6.4 403 — 권한 없는 principal (2줄)

```json
{
  "@timestamp": "2026-09-16T16:02:37.960Z",
  "_time": "2026-09-16T16:02:37.959325878Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Principal 'mx_1789574527_denied' with activated PrincipalRoles '[mx_1789574527_denied_role]' and activated grants via '[mx_1789574527_denied_role]' is not authorized for op LIST_NAMESPACES",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2068-listNamespaces-403",
    "realmId": "POLARIS"
  },
  "sequence": 44357
}
```

```json
{
  "@timestamp": "2026-09-16T16:02:37.960Z",
  "_time": "2026-09-16T16:02:37.960307965Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789574527_denied [16/Sep/2026:16:02:37 +0000] \"GET /api/catalog/v1/apimatrix1789574527_cat/namespaces HTTP/1.1\" 403 251",
  "user_principal_name": "mx_1789574527_denied",
  "client_ip": "192.168.194.1",
  "http_method": "GET",
  "api_path": "/api/catalog/v1/apimatrix1789574527_cat/namespaces",
  "http_status": 403,
  "response_size": 251,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2068-listNamespaces-403",
    "realmId": "POLARIS"
  },
  "sequence": 44358
}
```

#### 6.5 409 — 이미 존재하는 카탈로그 생성 (2줄)

```json
{
  "@timestamp": "2026-09-16T16:02:39.051Z",
  "_time": "2026-09-16T16:02:39.051440426Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Cannot create Catalog mx1789574527cat2. Catalog already exists or resolution failed",
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2269-createCatalog-409",
    "realmId": "POLARIS"
  },
  "sequence": 46030
}
```

```json
{
  "@timestamp": "2026-09-16T16:02:39.051Z",
  "_time": "2026-09-16T16:02:39.051594093Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [16/Sep/2026:16:02:39 +0000] \"POST /api/management/v1/catalogs HTTP/1.1\" 409 150",
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/management/v1/catalogs",
  "http_status": 409,
  "response_size": 150,
  "hostName": "benchmarks-polaris-777c948595-qnbxl",
  "mdc": {
    "requestId": "nb-1789574527-2269-createCatalog-409",
    "realmId": "POLARIS"
  },
  "sequence": 46031
}
```

---

## 7. 요약 — summary

윈도우당 정확히 1행입니다. **대시보드에서는 제외하고**(`not report_type:summary`) 완결성 검증에 씁니다. 불변식: `access_kept = access_seen − access_counted`, 그리고 `resource` 행의 `requests` 합 = `principal` 행의 `requests` 합 = `access_seen − parse_errors`. 사람이 읽는 문장 `message` 는 이 행에만 있습니다.

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "summary",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "partial_window": "false",
  "errors_4xx": 247,
  "errors_5xx": 4,
  "auth_denied": 104,
  "access_seen": 355,
  "access_kept": 200,
  "access_counted": 155,
  "counted_read": 31,
  "counted_post": 24,
  "counted_404": 100,
  "errors_kept": 151,
  "parse_errors": 0,
  "bytes_total": 1041865,
  "distinct_resources": 57,
  "distinct_principals": 4,
  "resources_other": 0,
  "resources_other_distinct": 0,
  "principals_other": 0,
  "role_keys_forced": 4,
  "app_dropped_total": 155,
  "app_dropped_404": 110,
  "held_orphans": 0,
  "held_pending": 0,
  "windows_skipped": 0,
  "min_record_time": "2026-09-16T16:02:36.572225313Z",
  "max_record_time": "2026-09-16T16:02:42.827385741Z",
  "message": "polaris shipper report seq=4@benchmarks-fluent-bit-62klp 2026-09-16T16:02:30Z..2026-09-16T16:03:00Z: 355 access lines, 200 kept, 155 counted (31 read, 24 POST, 100 404), 151 errors kept (247 4xx, 4 5xx, 104 denied), 57 resources, 4 principals, 155 app lines dropped, 1041865 bytes, 0 windows skipped"
}
```

> 이 윈도우 검증: resource `requests` 합 355, principal `requests` 합 355, `access_seen − parse_errors` = 355.

---

## 8. 요약 — principal

호출 주체별 1행. 요청 급증과 인증 거부(`auth_denied`) 급증을 여기서 봅니다. `"-"` 는 미인증 요청의 합계입니다. `errors_4xx` 에는 404 도 포함됩니다.

#### 8.1 `root`

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "principal",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "user_principal_name": "root",
  "requests": 110,
  "reads": 27,
  "writes": 83,
  "errors": 57,
  "errors_4xx": 57,
  "errors_5xx": 0,
  "auth_denied": 1,
  "response_bytes": 996349
}
```

#### 8.2 `mx_1789574527_runner`

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "principal",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "user_principal_name": "mx_1789574527_runner",
  "requests": 107,
  "reads": 26,
  "writes": 81,
  "errors": 59,
  "errors_4xx": 56,
  "errors_5xx": 3,
  "auth_denied": 1,
  "response_bytes": 28323
}
```

#### 8.3 `-`

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "principal",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "user_principal_name": "-",
  "requests": 79,
  "reads": 28,
  "writes": 51,
  "errors": 78,
  "errors_4xx": 77,
  "errors_5xx": 1,
  "auth_denied": 59,
  "response_bytes": 2926
}
```

#### 8.4 `mx_1789574527_denied`

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "principal",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "user_principal_name": "mx_1789574527_denied",
  "requests": 59,
  "reads": 25,
  "writes": 34,
  "errors": 57,
  "errors_4xx": 57,
  "errors_5xx": 0,
  "auth_denied": 43,
  "response_bytes": 14267
}
```

---

## 9. 요약 — resource

**키는 URL 이 아니라 리소스**입니다 (`/tables/t/metrics` 와 `/tables/t` 는 같은 행). 권한 부여는 롤 행으로 접히므로 롤 행의 `writes` 가 곧 부여 건수입니다. `last_read_bytes` / `last_write_bytes` 는 윈도우 안 마지막 성공 응답 크기, `commit_*` 는 **Iceberg 커밋 시간**(요청 지연 아님, 성공 건만)이며 평균은 `sum(commit_ms_sum) / sum(commit_count)` 로 구합니다.

#### 9.1 table — 요청과 커밋이 함께 있는 행

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns/tables/probe_tbl",
  "resource_kind": "table",
  "api_kind": "catalog",
  "requests": 36,
  "reads": 13,
  "writes": 23,
  "errors": 26,
  "errors_4xx": 26,
  "errors_5xx": 0,
  "auth_denied": 9,
  "response_bytes": 11570,
  "last_read_bytes": 1689,
  "last_write_bytes": 1941,
  "commit_count": 5,
  "commit_ms_sum": 101,
  "commit_ms_min": 8,
  "commit_ms_max": 40
}
```

#### 9.2 table — 다단계 네임스페이스 (`a%1Fb`) 에 커밋 2건

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns%1Fnested/tables/mx_1789574527_deep",
  "resource_kind": "table",
  "api_kind": "catalog",
  "requests": 3,
  "reads": 1,
  "writes": 2,
  "errors": 0,
  "errors_4xx": 0,
  "errors_5xx": 0,
  "auth_denied": 0,
  "response_bytes": 2539,
  "last_read_bytes": 1311,
  "last_write_bytes": 1228,
  "commit_count": 2,
  "commit_ms_sum": 40,
  "commit_ms_min": 14,
  "commit_ms_max": 26
}
```

#### 9.3 view

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns/views/mx_1789574527_vw2",
  "resource_kind": "view",
  "api_kind": "catalog",
  "requests": 1,
  "reads": 0,
  "writes": 1,
  "errors": 0,
  "errors_4xx": 0,
  "errors_5xx": 0,
  "auth_denied": 0,
  "response_bytes": 0,
  "commit_count": 2,
  "commit_ms_sum": 30,
  "commit_ms_min": 12,
  "commit_ms_max": 18
}
```

#### 9.4 namespace

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/catalog/v1/apimatrix1789574527_cat/namespaces/probe_ns",
  "resource_kind": "namespace",
  "api_kind": "catalog",
  "requests": 7,
  "reads": 6,
  "writes": 1,
  "errors": 4,
  "errors_4xx": 4,
  "errors_5xx": 0,
  "auth_denied": 4,
  "response_bytes": 373,
  "last_read_bytes": 114
}
```

#### 9.5 collection — 컬렉션 경로 (목록·생성)

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/catalog/v1/apimatrix1789574527_cat/namespaces",
  "resource_kind": "collection",
  "api_kind": "catalog",
  "requests": 10,
  "reads": 4,
  "writes": 6,
  "errors": 6,
  "errors_4xx": 5,
  "errors_5xx": 1,
  "auth_denied": 4,
  "response_bytes": 1231,
  "last_read_bytes": 53,
  "last_write_bytes": 130
}
```

#### 9.6 transaction — 다중 테이블 커밋

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/catalog/v1/apimatrix1789574527_cat/transactions/commit",
  "resource_kind": "transaction",
  "api_kind": "catalog",
  "requests": 5,
  "reads": 0,
  "writes": 5,
  "errors": 3,
  "errors_4xx": 3,
  "errors_5xx": 0,
  "auth_denied": 2,
  "response_bytes": 364
}
```

#### 9.7 catalog

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/management/v1/catalogs/apimatrix1789574527_cat",
  "resource_kind": "catalog",
  "api_kind": "management",
  "requests": 4,
  "reads": 3,
  "writes": 1,
  "errors": 3,
  "errors_4xx": 3,
  "errors_5xx": 0,
  "auth_denied": 2,
  "response_bytes": 910,
  "last_read_bytes": 531
}
```

#### 9.8 catalog-role — grant 가 접힌 행

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/management/v1/catalogs/apimatrix1789574527_cat/catalog-roles/mx_1789574527_crole",
  "resource_kind": "catalog-role",
  "api_kind": "management",
  "requests": 22,
  "reads": 10,
  "writes": 12,
  "errors": 12,
  "errors_4xx": 12,
  "errors_5xx": 0,
  "auth_denied": 9,
  "response_bytes": 1898,
  "last_read_bytes": 166
}
```

#### 9.9 principal-role

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/management/v1/principal-roles/mx_1789574527_runner_role",
  "resource_kind": "principal-role",
  "api_kind": "management",
  "requests": 11,
  "reads": 10,
  "writes": 1,
  "errors": 7,
  "errors_4xx": 7,
  "errors_5xx": 0,
  "auth_denied": 6,
  "response_bytes": 1434,
  "last_read_bytes": 180
}
```

#### 9.10 principal

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/management/v1/principals/mx_1789574527_p2",
  "resource_kind": "principal",
  "api_kind": "management",
  "requests": 13,
  "reads": 0,
  "writes": 13,
  "errors": 10,
  "errors_4xx": 10,
  "errors_5xx": 0,
  "auth_denied": 7,
  "response_bytes": 1461,
  "last_write_bytes": 294
}
```

#### 9.11 auth — OAuth 토큰

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/catalog/v1/oauth/tokens",
  "resource_kind": "auth",
  "api_kind": "catalog",
  "requests": 3,
  "reads": 0,
  "writes": 3,
  "errors": 2,
  "errors_4xx": 1,
  "errors_5xx": 1,
  "auth_denied": 1,
  "response_bytes": 982,
  "last_write_bytes": 757
}
```

#### 9.12 config

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "/api/catalog/v1/config",
  "resource_kind": "config",
  "api_kind": "catalog",
  "requests": 4,
  "reads": 4,
  "writes": 0,
  "errors": 2,
  "errors_4xx": 2,
  "errors_5xx": 0,
  "auth_denied": 1,
  "response_bytes": 4432,
  "last_read_bytes": 2171
}
```

#### 9.13 `__errors__` — 행을 만들 수 없는 오류 요청의 합계

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "resource",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "resource": "__errors__",
  "resource_kind": "error",
  "api_kind": "mixed",
  "requests": 65,
  "reads": 21,
  "writes": 44,
  "errors": 65,
  "errors_4xx": 65,
  "errors_5xx": 0,
  "auth_denied": 5,
  "response_bytes": 8559
}
```

> `__errors__`: 오류 요청은 새 행을 만들지 못합니다 (없는 이름을 두드리는 클라이언트가 행 상한을 채우지 못하게). 그 윈도우에 아직 행이 없던 리소스의 오류가 여기로 모이며, 원본 문서는 상세 인덱스에 전건 있습니다 (404 제외). 롤(`catalog-role`, `principal-role`)은 예외로 오류로도 행을 만듭니다.

---

## 10. 요약 — app_dropped

허용 목록 밖이라 적재하지 않은 애플리케이션 로그를 logger 별로 센 행입니다. 추이가 아니라 **허용 목록의 헬스 신호**입니다 — 처음 보는 `org.apache.polaris.service.*` logger 가 나타나면 Polaris 가 새 로그를 내기 시작했다는 뜻이고, 허용 목록 검토 대상입니다.

#### 10.1 `IcebergCatalogHandler`

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "app_dropped",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "logger_name": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler",
  "dropped": 60
}
```

#### 10.2 `BaseMetastoreCatalog`

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "app_dropped",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "logger_name": "org.apache.iceberg.BaseMetastoreCatalog",
  "dropped": 37
}
```

#### 10.3 `CatalogUtil`

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "app_dropped",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "logger_name": "org.apache.iceberg.CatalogUtil",
  "dropped": 30
}
```

#### 10.4 `IcebergCatalog`

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "app_dropped",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "logger_name": "org.apache.polaris.service.catalog.iceberg.IcebergCatalog",
  "dropped": 24
}
```

#### 10.5 `BaseMetastoreViewCatalog`

```json
{
  "@timestamp": "2026-09-16T16:03:01.721Z",
  "_time": "2026-09-16T16:03:00Z",
  "report_type": "app_dropped",
  "schema_version": 6,
  "report_seq": 4,
  "hostname": "benchmarks-fluent-bit-62klp",
  "window_start": "2026-09-16T16:02:30Z",
  "window_end": "2026-09-16T16:03:00Z",
  "window_seconds": 30,
  "logger_name": "org.apache.iceberg.view.BaseMetastoreViewCatalog",
  "dropped": 4
}
```

---

## 11. 검색 쿼리 예시 (DQL)

> **문자열 필드는 `.keyword` 로 검색합니다.** v6 인덱스 템플릿부터 선언되지 않은 문자열은 `.keyword` 에만 색인되고, 필드명만 쓰면 새 인덱스에서 0건이 나옵니다. `.keyword` 는 이전 인덱스에도 있으므로 아래 쿼리는 전 기간에 그대로 동작합니다. 숫자·`message`(전문 검색) 는 필드명 그대로 씁니다.

```text
# 상세 — polaris-logs-*
loggerName.keyword:"io.quarkus.http.access-log"
loggerName.keyword:"io.quarkus.http.access-log" and http_status >= 500
http_status:401 or http_status:403
user_principal_name.keyword:"mx_1789574527_denied"
level.keyword:"ERROR" and exception.exceptionType.keyword:*
mdc.requestId.keyword:"nb-1789574527-2268-renameView-400"
loggerName.keyword:"org.apache.polaris.service.admin.PolarisServiceImpl"
message:"Adding grant"
secret_redacted:true
access_log_parse_error:true

# 요약 — polaris-report-*
report_type.keyword:"summary"
report_type.keyword:"summary" and (errors_5xx > 0 or auth_denied > 0 or counted_404 > 0)
report_type.keyword:"principal" and window_start.keyword:"2026-09-16T16:02:30Z"
report_type.keyword:"resource" and errors_5xx > 0
report_type.keyword:"resource" and commit_count > 0
report_type.keyword:"app_dropped"
report_type.keyword:"summary" and partial_window.keyword:"true"
```

**조사 순서**: `report_type:summary` 로 이상 윈도우 발견 (`errors_5xx`, `auth_denied`, `counted_404` 급증) → 같은 `window_start` 의 `principal` / `resource` 행으로 범위 좁히기 → 그 시간대 상세 인덱스에서 실패 요청 찾기 → `mdc.requestId` 로 예외 · 스택 트레이스 · 서비스 로그 확인. 성공한 조회와 404 는 상세 인덱스에 없으므로 **요약 행의 숫자가 그 요청들의 유일한 기록**입니다.
