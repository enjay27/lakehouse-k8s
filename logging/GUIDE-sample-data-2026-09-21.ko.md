# OpenSearch 샘플 데이터 — `polaris-logs-*` (상세) · `polaris-report-*` (요약), 스키마 v6 — 2026-09-21

> 신규 엔지니어 공유용 샘플입니다. **이 문서는 손으로 쓴 것이 아니라 실제 export 에서 생성됩니다.**
> 다시 만들려면:
>
> ```bash
> python3 logging/scripts/step14-sample-doc.py <상세.json> <요약.json> > logging/GUIDE-sample-data-2026-09-21.ko.md
> ```
>
> - 원본: `polaris-logs-2026.09.21` 391건 · `polaris-report-2026.09.21` 122건 (Dev Tools export).
> - **값이 없는 필드는 싣지 않았습니다** (문서에 없는 필드, 빈 문자열, 빈 객체). 보이는 필드가 그 문서에 실제로 저장된 전부입니다.
> - 값은 저장된 타입 그대로입니다 — 숫자는 숫자(`403`, `184`), 불리언은 불리언. (Dashboards CSV export 와 달리 쉼표 포맷·문자열 변환이 없습니다.)
> - `message` 의 줄바꿈은 JSON 규칙에 따라 `\n` 으로 이스케이프했습니다. Dev Tools 응답 패널을 거쳤기 때문에 **여러 줄 `message` 의 들여쓰기 공백은 원본과 다를 수 있습니다** (값의 내용은 같음).
> - `clientSecret` 은 Polaris 가 로그에 이미 `*` 로 마스킹해 남깁니다. 마스킹이 빠진 값이 들어오면 파이프라인이 `<redacted>` 로 바꾸고 `secret_redacted: true` 를 붙입니다.
> - 시간대: `@timestamp` · `_time` 은 UTC (`Z`). KST 는 +9 시간입니다. access log `message` 안의 시간도 UTC(+0000).
> - **스키마 v6 기준.** 리포트 행에는 `app`·`level`·`_msg` 가 없고, 원문 필드 이름은 `message` 입니다.
>   상세 문서의 **`threadName`·`threadId` 는 2026-09-18 에 복원됐습니다**(`#42`) — 2026-09-16 판 문서는 이 둘이 없다고 적고 있는데, 그 서술은 09-19 이후 인덱스에는 맞지 않습니다.
> - ⚠ **문자열 조회는 `.keyword` 로 합니다.** `threadName.keyword`, `loggerName.keyword` — 맨 이름으로 `term`/`exists` 를 걸면 0건입니다 (§11).

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

- **상세 `polaris-logs-2026.09.21`** (391건): Polaris 파드 `benchmarks-polaris-c7c64b9dd-cwb8k` 의 로그 중 **적재 대상만** 남은 문서.
  2026-09-21T04:43:48.004Z ~ 2026-09-21T04:44:13.070Z
  - `io.quarkus.http.access-log` 245건 (INFO 245)
  - `org.apache.polaris.service.exception.IcebergExceptionMapper` 82건 (ERROR 7 / INFO 75)
  - `org.apache.polaris.service.admin.PolarisServiceImpl` 62건 (INFO 62)
  - `org.apache.polaris.service.events.PolarisEventListeners` 2건 (ERROR 2)
- **요약 `polaris-report-2026.09.21`** (122건): Fluent Bit 파드 `benchmarks-fluent-bit-pdr2h` 가 윈도우
  `2026-09-21T04:32:30Z` ~ `2026-09-21T04:47:30Z` (30초, 검증용 길이; 운영 설계값은 30분) 를 닫으며 만든 행. 윈도우 30개.
  - `report_type`: `summary` 30 / `principal` 7 / `resource` 77 / `app_dropped` 8
- **트래픽은 윈도우 2개에만 있습니다.** 나머지 28개는 `access_seen: 0` 인 빈 summary 행입니다 — 30초 윈도우를 쓰는 동안은 이렇게 빈 행이 대부분을 차지합니다.
- **적재되지 않은 것은 요약에 숫자로 남습니다.** 이 구간의 access log 는 **443줄**이었고 그중 **245줄**만 상세 인덱스에 있습니다.
  나머지 198줄(성공한 조회 66, catalog POST 33, **404 99**)은 `summary`·`resource`·`principal` 행의 카운터로만 존재합니다.
  허용 목록 밖 애플리케이션 로그 124줄은 `app_dropped` 행에, 404 요청에 딸린 앱 로그 109줄은 `summary.app_dropped_404` 에 있습니다.
- 상세 인덱스의 access 문서 245건은 `access_kept` 245 과 일치하고, 앱 로그 146건이 더해져 391건입니다.
- 오류 분포: `200` 5건, `201` 57건, `204` 33건, `400` 19건, `401` 60건, `403` 50건, `409` 14건, `500` 7건 — `errors_4xx` 242, `errors_5xx` 7, `auth_denied` 110 (404 집계분 포함).
- 권한 매트릭스 테스트가 일부러 에러를 유발한 실행이라 에러 비율이 운영보다 훨씬 높습니다.
- 같은 요청의 로그는 `mdc.requestId` 로, 같은 집계 윈도우의 요약 행은 `window_start` + `hostname` (또는 `report_seq` + `hostname`) 으로 묶입니다.

---

## 2. 상세 — HTTP Access Log

`message` 는 Quarkus 액세스 로그 원문이고, 파이프라인이 그것을 `client_ip` · `user_principal_name` · `http_method` · `api_path` · `http_status` · `response_size` 로 분해합니다. `user_principal_name: "-"` 는 결측이 아니라 **미인증/인증 실패**입니다.

**404 는 여기에 없습니다** — 정책 v5 는 404 를 세기만 하고 문서로 남기지 않습니다 (이 구간 99건).

#### 2.1 200 OK — PUT (management API)

```json
{
  "@timestamp": "2026-09-21T04:44:07.514Z",
  "_time": "2026-09-21T04:44:07.514435465Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [21/Sep/2026:04:44:07 +0000] \"PUT /api/management/v1/catalogs/mx1789965827cat2 HTTP/1.1\" 200 543",
  "threadName": "executor-thread-16",
  "threadId": 57,
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "PUT",
  "api_path": "/api/management/v1/catalogs/mx1789965827cat2",
  "http_status": 200,
  "response_size": 543,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2037-updateCatalog-2",
    "realmId": "POLARIS"
  },
  "sequence": 4548
}
```

#### 2.2 201 Created — POST (management API)

```json
{
  "@timestamp": "2026-09-21T04:43:48.004Z",
  "_time": "2026-09-21T04:43:48.004165986Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - root [21/Sep/2026:04:43:48 +0000] \"POST /api/management/v1/principals HTTP/1.1\" 201 273",
  "threadName": "executor-thread-16",
  "threadId": 57,
  "user_principal_name": "root",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/management/v1/principals",
  "http_status": 201,
  "response_size": 273,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "a8fdbd69-13cc-4d83-8907-0b52bf463dd9_0000000000000000324",
    "realmId": "POLARIS"
  },
  "sequence": 4307
}
```

#### 2.3 204 No Content — DELETE (catalog API)

```json
{
  "@timestamp": "2026-09-21T04:44:06.590Z",
  "_time": "2026-09-21T04:44:06.590232342Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789965827_runner [21/Sep/2026:04:44:06 +0000] \"DELETE /api/catalog/v1/apimatrix1789965827_cat/namespaces/mx_1789965827_ns_doomed HTTP/1.1\" 204 -",
  "threadName": "executor-thread-17",
  "threadId": 58,
  "user_principal_name": "mx_1789965827_runner",
  "client_ip": "192.168.194.1",
  "http_method": "DELETE",
  "api_path": "/api/catalog/v1/apimatrix1789965827_cat/namespaces/mx_1789965827_ns_doomed",
  "http_status": 204,
  "response_size": 0,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2005-dropNamespace-2",
    "realmId": "POLARIS"
  },
  "sequence": 4471
}
```

#### 2.4 400 Bad Request — POST (catalog API)

```json
{
  "@timestamp": "2026-09-21T04:44:06.693Z",
  "_time": "2026-09-21T04:44:06.693272039Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789965827_runner [21/Sep/2026:04:44:06 +0000] \"POST /api/catalog/v1/apimatrix1789965827_cat/namespaces/probe_ns/register-view HTTP/1.1\" 400 171",
  "threadName": "executor-thread-19",
  "threadId": 61,
  "user_principal_name": "mx_1789965827_runner",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/apimatrix1789965827_cat/namespaces/probe_ns/register-view",
  "http_status": 400,
  "response_size": 171,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2010-registerView-2",
    "realmId": "POLARIS"
  },
  "sequence": 4479
}
```

#### 2.5 401 Unauthorized — GET (catalog API)

```json
{
  "@timestamp": "2026-09-21T04:44:07.893Z",
  "_time": "2026-09-21T04:44:07.893029084Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - - [21/Sep/2026:04:44:07 +0000] \"GET /api/catalog/v1/config?warehouse=apimatrix1789965827_cat HTTP/1.1\" 401 -",
  "threadName": "vert.x-eventloop-thread-0",
  "threadId": 30,
  "user_principal_name": "-",
  "client_ip": "192.168.194.1",
  "http_method": "GET",
  "api_path": "/api/catalog/v1/config?warehouse=apimatrix1789965827_cat",
  "http_status": 401,
  "response_size": 0,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2066-getConfig-401",
    "realmId": "POLARIS"
  },
  "sequence": 4589
}
```

#### 2.6 403 Forbidden — POST (catalog API)

```json
{
  "@timestamp": "2026-09-21T04:44:06.646Z",
  "_time": "2026-09-21T04:44:06.646396252Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789965827_runner [21/Sep/2026:04:44:06 +0000] \"POST /api/catalog/v1/apimatrix1789965827_cat/namespaces/probe_ns/register HTTP/1.1\" 403 380",
  "threadName": "executor-thread-19",
  "threadId": 61,
  "user_principal_name": "mx_1789965827_runner",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/apimatrix1789965827_cat/namespaces/probe_ns/register",
  "http_status": 403,
  "response_size": 380,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2009-registerTable-2",
    "realmId": "POLARIS"
  },
  "sequence": 4476
}
```

#### 2.7 409 Conflict — POST (catalog API)

```json
{
  "@timestamp": "2026-09-21T04:44:08.850Z",
  "_time": "2026-09-21T04:44:08.84995787Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789965827_runner [21/Sep/2026:04:44:08 +0000] \"POST /api/catalog/v1/apimatrix1789965827_cat/namespaces HTTP/1.1\" 409 134",
  "threadName": "executor-thread-17",
  "threadId": 58,
  "user_principal_name": "mx_1789965827_runner",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/apimatrix1789965827_cat/namespaces",
  "http_status": 409,
  "response_size": 134,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2254-createNamespace-409",
    "realmId": "POLARIS"
  },
  "sequence": 4918
}
```

#### 2.8 500 Internal Server Error — POST (catalog API)

```json
{
  "@timestamp": "2026-09-21T04:44:08.838Z",
  "_time": "2026-09-21T04:44:08.838208142Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - - [21/Sep/2026:04:44:08 +0000] \"POST /api/catalog/v1/oauth/tokens HTTP/1.1\" 500 126",
  "threadName": "executor-thread-17",
  "threadId": 58,
  "user_principal_name": "-",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/oauth/tokens",
  "http_status": 500,
  "response_size": 126,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2253-getToken-400",
    "realmId": "POLARIS"
  },
  "sequence": 4916
}
```

---

## 3. 상세 — Admin 감사 로그 (PolarisServiceImpl)

관리 API 가 "무엇을 바꿨는지" 를 남기는 로그입니다. 액세스 로그가 *요청*을 기록한다면 이쪽은 *결과*를 기록합니다 — 둘은 `mdc.requestId` 로 조인합니다.

#### 3.1 Created new principal class PrincipalWithCredentials {

```json
{
  "@timestamp": "2026-09-21T04:43:48.004Z",
  "_time": "2026-09-21T04:43:48.001719714Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Created new principal class PrincipalWithCredentials {\n    principal: class Principal {\n        name: mx_1789965827_denied\n        clientId: 85ef6829072aa181\n        properties: {}\n        createTimestamp: 1789965827989\n        lastUpdateTimestamp: 1789965827989\n        entityVersion: 1\n    }\n    credentials: class PrincipalWithCredentialsCredentials {\n        clientId: 85ef6829072aa181\n        clientSecret: *\n    }\n}",
  "threadName": "executor-thread-16",
  "threadId": 57,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "a8fdbd69-13cc-4d83-8907-0b52bf463dd9_0000000000000000324",
    "realmId": "POLARIS"
  },
  "sequence": 4306
}
```

#### 3.2 Created new principalRole class PrincipalRole {

```json
{
  "@timestamp": "2026-09-21T04:43:48.068Z",
  "_time": "2026-09-21T04:43:48.066347657Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Created new principalRole class PrincipalRole {\n    name: mx_1789965827_denied_role\n    federated: false\n    properties: {}\n    createTimestamp: 1789965828063\n    lastUpdateTimestamp: 1789965828063\n    entityVersion: 1\n}",
  "threadName": "executor-thread-16",
  "threadId": 57,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "a8fdbd69-13cc-4d83-8907-0b52bf463dd9_0000000000000000325",
    "realmId": "POLARIS"
  },
  "sequence": 4308
}
```

#### 3.3 Assigning principalRole mx_1789965827_denied_role to principal mx_1789

```json
{
  "@timestamp": "2026-09-21T04:43:48.153Z",
  "_time": "2026-09-21T04:43:48.092129259Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Assigning principalRole mx_1789965827_denied_role to principal mx_1789965827_denied",
  "threadName": "executor-thread-16",
  "threadId": 57,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "a8fdbd69-13cc-4d83-8907-0b52bf463dd9_0000000000000000326",
    "realmId": "POLARIS"
  },
  "sequence": 4310
}
```

#### 3.4 Created new catalog class PolarisCatalog {

```json
{
  "@timestamp": "2026-09-21T04:43:48.367Z",
  "_time": "2026-09-21T04:43:48.36611925Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.admin.PolarisServiceImpl",
  "message": "Created new catalog class PolarisCatalog {\n    class Catalog {\n        type: INTERNAL\n        name: apimatrix1789965827_cat\n        properties: class CatalogProperties {\n            {polaris.config.drop-with-purge.enabled=true, default-base-location=s3a://data-catalog-bucket/apimatrix1789965827_cat/}\n            defaultBaseLocation: s3a://data-catalog-bucket/apimatrix1789965827_cat/\n        }\n        createTimestamp: 1789965828296\n        lastUpdateTimestamp: 0\n        entityVersion: 1\n        storageConfigInfo: class AwsStorageConfigInfo {\n            class StorageConfigInfo {\n                storageType: S3\n                allowedLocations: [s3a://data-catalog-bucket/apimatrix1789965827_cat/, s3a://data-catalog-bucket/]\n                storageName: null\n            }\n            roleArn: null\n            externalId: null\n            userArn: null\n            currentKmsKey: null\n            allowedKmsKeys: []\n            region: null\n            endpoint: http://192.168.139.2:9000\n            stsEndpoint: null\n            stsUnavailable: null\n            endpointInternal: http://192.168.139.2:9000\n            pathStyleAccess: true\n            kmsUnavailable: null\n        }\n    }\n}",
  "threadName": "executor-thread-16",
  "threadId": 57,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "a8fdbd69-13cc-4d83-8907-0b52bf463dd9_0000000000000000330",
    "realmId": "POLARIS"
  },
  "sequence": 4317
}
```

---

## 4. 상세 — Exception Mapper (INFO)

`IcebergExceptionMapper` 는 예외를 HTTP 응답으로 바꾸면서 **왜 실패했는지**를 남깁니다. `INFO` 는 "정상적으로 거부한" 경우입니다 — 권한 없음, 이미 있음, 잘못된 입력. 같은 요청의 액세스 로그(4xx)와 짝입니다.

#### 4.1 Handling runtimeException Invalid locations '[s3a://data-catalog-bucke

```json
{
  "@timestamp": "2026-09-21T04:44:06.646Z",
  "_time": "2026-09-21T04:44:06.645904915Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Invalid locations '[s3a://data-catalog-bucket/mx1789965827cat2/never-registered/metadata.json]' for identifier 'probe_ns.mx_1789965827_tbl2': s3a://data-catalog-bucket/mx1789965827cat2/never-registered/metadata.json is not in the list of allowed locations: [s3a://data-catalog-bucket/apimatrix1789965827_cat/probe_ns]",
  "threadName": "executor-thread-19",
  "threadId": 61,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2009-registerTable-2",
    "realmId": "POLARIS"
  },
  "sequence": 4475
}
```

#### 4.2 Handling runtimeException s3a://data-catalog-bucket/mx1789965827cat2/n

```json
{
  "@timestamp": "2026-09-21T04:44:06.693Z",
  "_time": "2026-09-21T04:44:06.692670784Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException s3a://data-catalog-bucket/mx1789965827cat2/never-registered/metadata.json is not a valid metadata file",
  "threadName": "executor-thread-19",
  "threadId": 61,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2010-registerView-2",
    "realmId": "POLARIS"
  },
  "sequence": 4478
}
```

#### 4.3 Handling runtimeException Principal 'root' with activated PrincipalRol

```json
{
  "@timestamp": "2026-09-21T04:44:07.861Z",
  "_time": "2026-09-21T04:44:07.860797384Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Principal 'root' with activated PrincipalRoles '[service_admin]' and activated grants via '[service_admin]' is not authorized for op ROTATE_CREDENTIALS",
  "threadName": "executor-thread-16",
  "threadId": 57,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2065-rotateCredentials-2",
    "realmId": "POLARIS"
  },
  "sequence": 4587
}
```

---

## 5. 상세 — ERROR + Stack Trace

**규칙 1: `ERROR` 와 `WARN` 은 허용 목록과 무관하게 무조건 적재됩니다.** 그래서 이 절의 문서에는 `APP_ALLOW` 에 없는 logger 도 나옵니다 — 새 logger 가 조용히 사라지지 않게 하려는 설계입니다.

이 구간의 ERROR/WARN 은 9건입니다.

#### 5.1 `IcebergExceptionMapper` — java.lang.NullPointerException

```json
{
  "@timestamp": "2026-09-21T04:44:08.838Z",
  "_time": "2026-09-21T04:44:08.837862764Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "threadName": "executor-thread-17",
  "threadId": 58,
  "exception": {
    "refId": 1,
    "exceptionType": "java.lang.NullPointerException",
    "message": "Cannot invoke \"Object.equals(Object)\" because \"o\" is null",
    "frames": [
      {"class": "java.util.ImmutableCollections$Set12", "method": "contains", "line": 817},
      {"class": "org.apache.polaris.service.auth.internal.broker.JWTBroker", "method": "supportsGrantType", "line": 179},
      {"class": "org.apache.polaris.service.auth.internal.broker.ServiceProducers_ProducerMethod_tokenBroker_pKyuSLrp6V1EV14KaXDBTA1e90o_ClientProxy", "method": "supportsGrantType"},
      {"class": "org.apache.polaris.service.auth.internal.service.DefaultOAuth2ApiService", "method": "getToken", "line": 72},
      {"class": "org.apache.polaris.service.auth.internal.service.DefaultOAuth2ApiService_ClientProxy", "method": "getToken"},
      {"class": "org.apache.polaris.service.catalog.api.ServiceProducers_ProducerMethod_icebergRestOAuth2ApiService_MtUuMFyhMWQ9p67dec6El1hvgiM_ClientProxy", "method": "getToken"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api", "method": "getToken", "line": 99},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api_Subclass", "method": "getToken$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api_Subclass$0", "method": "apply"},
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
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 190},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 695},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ]
  },
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2253-getToken-400",
    "realmId": "POLARIS"
  },
  "sequence": 4915
}
```

#### 5.2 `IcebergExceptionMapper` — java.lang.NullPointerException

```json
{
  "@timestamp": "2026-09-21T04:44:08.858Z",
  "_time": "2026-09-21T04:44:08.857415977Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "threadName": "executor-thread-17",
  "threadId": 58,
  "exception": {
    "refId": 1,
    "exceptionType": "java.lang.NullPointerException",
    "message": "Cannot invoke \"org.apache.iceberg.catalog.Namespace.levels()\" because \"namespace\" is null",
    "frames": [
      {"class": "org.apache.polaris.service.catalog.validation.EntityNameValidator", "method": "validateNamespace", "line": 78},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "createNamespace", "line": 138},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createNamespace$$superforward"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "createNamespace"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "createNamespace", "line": 110},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createNamespace"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "createNamespace"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "createNamespace", "line": 158},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createNamespace$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$1", "method": "apply"},
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
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 31},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 48},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor$RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
      {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createNamespace"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$createNamespace_2f4cb7ed21ec4ad54465312433c6a6bb85723a70", "method": "invoke"},
      {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 190},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 695},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ]
  },
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-2255-createNamespace-400",
    "realmId": "POLARIS"
  },
  "sequence": 4920
}
```

#### 5.3 `PolarisEventListeners` — java.lang.NullPointerException

```json
{
  "@timestamp": "2026-09-21T04:44:09.323Z",
  "_time": "2026-09-21T04:44:09.323227446Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.events.PolarisEventListeners",
  "message": "Error while delivering BEFORE_RENAME_TABLE event to listener 'persistence-in-memory-buffer' (org.apache.polaris.service.events.listeners.inmemory.InMemoryBufferEventListener_Subclass@3cfbe489)",
  "threadName": "executor-thread-17",
  "threadId": 58,
  "exception": {
    "refId": 1,
    "exceptionType": "java.lang.NullPointerException",
    "message": "Cannot invoke \"org.apache.iceberg.catalog.TableIdentifier.toString()\" because the return value of \"org.apache.iceberg.rest.requests.RenameTableRequest.source()\" is null",
    "frames": [
      {"class": "org.apache.polaris.service.events.listeners.PolarisPersistenceEventListener", "method": "lambda$resolveRenameIdentifier$7", "line": 180},
      {"class": "java.util.Optional", "method": "map", "line": 260},
      {"class": "org.apache.polaris.service.events.listeners.PolarisPersistenceEventListener", "method": "resolveRenameIdentifier", "line": 176},
      {"class": "org.apache.polaris.service.events.listeners.PolarisPersistenceEventListener", "method": "resolveTableResourceIdentifier", "line": 120},
      {"class": "org.apache.polaris.service.events.listeners.PolarisPersistenceEventListener", "method": "resolveResourceIdentifier", "line": 103},
      {"class": "org.apache.polaris.service.events.listeners.PolarisPersistenceEventListener", "method": "onEvent", "line": 49},
      {"class": "org.apache.polaris.service.events.listeners.inmemory.InMemoryBufferEventListener_ClientProxy", "method": "onEvent"},
      {"class": "org.apache.polaris.service.events.PolarisEventListeners", "method": "deliverEvent", "line": 150},
      {"class": "org.apache.polaris.service.events.PolarisEventListeners", "method": "lambda$scheduleEventDelivery$1", "line": 127},
      {"class": "org.apache.polaris.service.events.PolarisEventListeners$ListenerExecutor", "method": "drain", "line": 209},
      {"class": "java.util.concurrent.CompletableFuture$AsyncRun", "method": "run", "line": 1804},
      {"class": "io.smallrye.context.impl.wrappers.SlowContextualRunnable", "method": "run", "line": 19},
      {"class": "org.jboss.threads.EnhancedViewExecutor$EnhancedViewExecutorRunnable", "method": "run", "line": 496},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 695},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ]
  },
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "sequence": 4984
}
```

#### 5.4 `IcebergExceptionMapper` — software.amazon.awssdk.core.exception.SdkClientException

```json
{
  "@timestamp": "2026-09-21T04:44:10.356Z",
  "_time": "2026-09-21T04:44:10.352682911Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "threadName": "executor-thread-19",
  "threadId": 61,
  "exception": {
    "refId": 1,
    "exceptionType": "software.amazon.awssdk.core.exception.SdkClientException",
    "message": "Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused (SDK Attempt Count: 4)",
    "frames": [
      {"class": "software.amazon.awssdk.core.exception.SdkClientException$BuilderImpl", "method": "build", "line": 130},
      {"class": "software.amazon.awssdk.core.exception.SdkClientException$BuilderImpl", "method": "build", "line": 95},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.utils.RetryableStageHelper", "method": "retryPolicyDisallowedRetryException", "line": 180},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 86},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 39},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
      {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 53},
      {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 35},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "executeWithTimer", "line": 82},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 62},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 43},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 50},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 32},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 37},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 26},
      {"class": "software.amazon.awssdk.core.internal.http.AmazonSyncHttpClient$RequestExecutionBuilderImpl", "method": "execute", "line": 210},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "invoke", "line": 103},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "doExecute", "line": 173},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "lambda$execute$1", "line": 80},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "measureApiCallSuccess", "line": 182},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "execute", "line": 74},
      {"class": "software.amazon.awssdk.core.client.handler.SdkSyncClientHandler", "method": "execute", "line": 45},
      {"class": "software.amazon.awssdk.awscore.client.handler.AwsSyncClientHandler", "method": "execute", "line": 53},
      {"class": "software.amazon.awssdk.services.sts.DefaultStsClient", "method": "assumeRole", "line": 292},
      {"class": "org.apache.polaris.core.storage.aws.AwsCredentialsStorageIntegration", "method": "compute", "line": 251},
      {"class": "org.apache.polaris.core.storage.aws.AwsStorageCredentialCacheKey", "method": "load", "line": 83},
      {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "lambda$new$1", "line": 66},
      {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "lambda$newMappingFunction$0", "line": 192},
      {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "lambda$doComputeIfAbsent$0", "line": 2767},
      {"class": "java.util.concurrent.ConcurrentHashMap", "method": "compute", "line": 1916},
      {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "doComputeIfAbsent", "line": 2765},
      {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "computeIfAbsent", "line": 2756},
      {"class": "com.github.benmanes.caffeine.cache.LocalCache", "method": "computeIfAbsent", "line": 132},
      {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "get", "line": 60},
      {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "getOrLoad", "line": 94},
      {"class": "org.apache.polaris.core.storage.cache.ServiceProducers_ProducerMethod_storageCredentialCache_7RHD-esc0KR78_Ued1hDYZdCCAg_ClientProxy", "method": "getOrLoad"},
      {"class": "org.apache.polaris.core.storage.CachingStorageIntegration", "method": "getStorageAccessConfig", "line": 76},
      {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 135},
      {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 88},
      {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider_ClientProxy", "method": "getStorageAccessConfig"},
      {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog", "method": "loadFileIOForTableLike", "line": 2403},
      {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "doCommit", "line": 1742},
      {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "commit", "line": 1597},
      {"class": "org.apache.iceberg.BaseMetastoreCatalog$BaseMetastoreCatalogTableBuilder", "method": "create", "line": 201},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "createTableDirect", "line": 489},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$createTable$7", "line": 300},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalogByName", "line": 114},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 106},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "createTable", "line": 284},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable$$superforward"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "createTable"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "createTable", "line": 323},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "createTable"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "createTable", "line": 198},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$2", "method": "apply"},
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
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 31},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 48},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor$RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
      {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$createTable_a10bf5c238b8901b2eb111a115d60b2d128401c9", "method": "invoke"},
      {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 190},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 695},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ],
    "suppressed": [
      {
        "refId": 2,
        "exceptionType": "software.amazon.awssdk.core.exception.SdkClientException",
        "message": "Request attempt 1 failure: Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused",
        "frames": []
      },
      {
        "refId": 3,
        "exceptionType": "software.amazon.awssdk.core.exception.SdkClientException",
        "message": "Request attempt 2 failure: Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused",
        "frames": []
      },
      {
        "refId": 4,
        "exceptionType": "software.amazon.awssdk.core.exception.SdkClientException",
        "message": "Request attempt 3 failure: Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused",
        "frames": []
      }
    ],
    "causedBy": {
      "exception": {
        "refId": 5,
        "exceptionType": "org.apache.http.conn.HttpHostConnectException",
        "message": "Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused",
        "frames": [
          {"class": "org.apache.http.impl.conn.DefaultHttpClientConnectionOperator", "method": "connect", "line": 156},
          {"class": "org.apache.http.impl.conn.PoolingHttpClientConnectionManager", "method": "connect", "line": 376},
          {"class": "software.amazon.awssdk.http.apache.internal.conn.ClientConnectionManagerFactory$DelegatingHttpClientConnectionManager", "method": "connect", "line": 86},
          {"class": "org.apache.http.impl.execchain.MainClientExec", "method": "establishRoute", "line": 393},
          {"class": "org.apache.http.impl.execchain.MainClientExec", "method": "execute", "line": 236},
          {"class": "org.apache.http.impl.execchain.ProtocolExec", "method": "execute", "line": 186},
          {"class": "org.apache.http.impl.client.InternalHttpClient", "method": "doExecute", "line": 185},
          {"class": "org.apache.http.impl.client.CloseableHttpClient", "method": "execute", "line": 83},
          {"class": "org.apache.http.impl.client.CloseableHttpClient", "method": "execute", "line": 56},
          {"class": "software.amazon.awssdk.http.apache.internal.impl.ApacheSdkHttpClient", "method": "execute", "line": 72},
          {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient", "method": "execute", "line": 261},
          {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient", "method": "access$600", "line": 106},
          {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient$1", "method": "call", "line": 238},
          {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient$1", "method": "call", "line": 235},
          {"class": "software.amazon.awssdk.core.internal.util.MetricUtils", "method": "measureDurationUnsafe", "line": 103},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "executeHttpRequest", "line": 92},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "execute", "line": 68},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "execute", "line": 50},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage", "method": "execute", "line": 74},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage", "method": "execute", "line": 43},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage", "method": "execute", "line": 79},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage", "method": "execute", "line": 41},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage", "method": "execute", "line": 58},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage", "method": "execute", "line": 41},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "executeRequest", "line": 106},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 62},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 39},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 53},
          {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 35},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "executeWithTimer", "line": 82},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 62},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 43},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 50},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 32},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 37},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 26},
          {"class": "software.amazon.awssdk.core.internal.http.AmazonSyncHttpClient$RequestExecutionBuilderImpl", "method": "execute", "line": 210},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "invoke", "line": 103},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "doExecute", "line": 173},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "lambda$execute$1", "line": 80},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "measureApiCallSuccess", "line": 182},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "execute", "line": 74},
          {"class": "software.amazon.awssdk.core.client.handler.SdkSyncClientHandler", "method": "execute", "line": 45},
          {"class": "software.amazon.awssdk.awscore.client.handler.AwsSyncClientHandler", "method": "execute", "line": 53},
          {"class": "software.amazon.awssdk.services.sts.DefaultStsClient", "method": "assumeRole", "line": 292},
          {"class": "org.apache.polaris.core.storage.aws.AwsCredentialsStorageIntegration", "method": "compute", "line": 251},
          {"class": "org.apache.polaris.core.storage.aws.AwsStorageCredentialCacheKey", "method": "load", "line": 83},
          {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "lambda$new$1", "line": 66},
          {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "lambda$newMappingFunction$0", "line": 192},
          {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "lambda$doComputeIfAbsent$0", "line": 2767},
          {"class": "java.util.concurrent.ConcurrentHashMap", "method": "compute", "line": 1916},
          {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "doComputeIfAbsent", "line": 2765},
          {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "computeIfAbsent", "line": 2756},
          {"class": "com.github.benmanes.caffeine.cache.LocalCache", "method": "computeIfAbsent", "line": 132},
          {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "get", "line": 60},
          {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "getOrLoad", "line": 94},
          {"class": "org.apache.polaris.core.storage.cache.ServiceProducers_ProducerMethod_storageCredentialCache_7RHD-esc0KR78_Ued1hDYZdCCAg_ClientProxy", "method": "getOrLoad"},
          {"class": "org.apache.polaris.core.storage.CachingStorageIntegration", "method": "getStorageAccessConfig", "line": 76},
          {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 135},
          {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 88},
          {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider_ClientProxy", "method": "getStorageAccessConfig"},
          {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog", "method": "loadFileIOForTableLike", "line": 2403},
          {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "doCommit", "line": 1742},
          {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "commit", "line": 1597},
          {"class": "org.apache.iceberg.BaseMetastoreCatalog$BaseMetastoreCatalogTableBuilder", "method": "create", "line": 201},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "createTableDirect", "line": 489},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$createTable$7", "line": 300},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalogByName", "line": 114},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 106},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "createTable", "line": 284},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable$$superforward"},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "createTable"},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "createTable", "line": 323},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable"},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "createTable"},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "createTable", "line": 198},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable$$superforward"},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$2", "method": "apply"},
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
          {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 31},
          {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
          {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
          {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
          {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
          {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 48},
          {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor$RolesAllowedInterceptor_Bean", "method": "intercept"},
          {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
          {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
          {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable"},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$createTable_a10bf5c238b8901b2eb111a115d60b2d128401c9", "method": "invoke"},
          {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
          {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 190},
          {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
          {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 695},
          {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
          {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
          {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
          {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
          {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
          {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
          {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
          {"class": "java.lang.Thread", "method": "run", "line": 1583}
        ],
        "causedBy": {
          "exception": {
            "refId": 6,
            "exceptionType": "java.net.ConnectException",
            "message": "Connection refused",
            "frames": [
              {"class": "sun.nio.ch.Net", "method": "pollConnect"},
              {"class": "sun.nio.ch.Net", "method": "pollConnectNow", "line": 694},
              {"class": "sun.nio.ch.NioSocketImpl", "method": "timedFinishConnect", "line": 542},
              {"class": "sun.nio.ch.NioSocketImpl", "method": "connect", "line": 592},
              {"class": "java.net.SocksSocketImpl", "method": "connect", "line": 327},
              {"class": "java.net.Socket", "method": "connect", "line": 751},
              {"class": "org.apache.http.conn.socket.PlainConnectionSocketFactory", "method": "connectSocket", "line": 75},
              {"class": "org.apache.http.impl.conn.DefaultHttpClientConnectionOperator", "method": "connect", "line": 142},
              {"class": "org.apache.http.impl.conn.PoolingHttpClientConnectionManager", "method": "connect", "line": 376},
              {"class": "software.amazon.awssdk.http.apache.internal.conn.ClientConnectionManagerFactory$DelegatingHttpClientConnectionManager", "method": "connect", "line": 86},
              {"class": "org.apache.http.impl.execchain.MainClientExec", "method": "establishRoute", "line": 393},
              {"class": "org.apache.http.impl.execchain.MainClientExec", "method": "execute", "line": 236},
              {"class": "org.apache.http.impl.execchain.ProtocolExec", "method": "execute", "line": 186},
              {"class": "org.apache.http.impl.client.InternalHttpClient", "method": "doExecute", "line": 185},
              {"class": "org.apache.http.impl.client.CloseableHttpClient", "method": "execute", "line": 83},
              {"class": "org.apache.http.impl.client.CloseableHttpClient", "method": "execute", "line": 56},
              {"class": "software.amazon.awssdk.http.apache.internal.impl.ApacheSdkHttpClient", "method": "execute", "line": 72},
              {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient", "method": "execute", "line": 261},
              {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient", "method": "access$600", "line": 106},
              {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient$1", "method": "call", "line": 238},
              {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient$1", "method": "call", "line": 235},
              {"class": "software.amazon.awssdk.core.internal.util.MetricUtils", "method": "measureDurationUnsafe", "line": 103},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "executeHttpRequest", "line": 92},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "execute", "line": 68},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "execute", "line": 50},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage", "method": "execute", "line": 74},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage", "method": "execute", "line": 43},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage", "method": "execute", "line": 79},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage", "method": "execute", "line": 41},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage", "method": "execute", "line": 58},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage", "method": "execute", "line": 41},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "executeRequest", "line": 106},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 62},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 39},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 53},
              {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 35},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "executeWithTimer", "line": 82},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 62},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 43},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 50},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 32},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 37},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 26},
              {"class": "software.amazon.awssdk.core.internal.http.AmazonSyncHttpClient$RequestExecutionBuilderImpl", "method": "execute", "line": 210},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "invoke", "line": 103},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "doExecute", "line": 173},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "lambda$execute$1", "line": 80},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "measureApiCallSuccess", "line": 182},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "execute", "line": 74},
              {"class": "software.amazon.awssdk.core.client.handler.SdkSyncClientHandler", "method": "execute", "line": 45},
              {"class": "software.amazon.awssdk.awscore.client.handler.AwsSyncClientHandler", "method": "execute", "line": 53},
              {"class": "software.amazon.awssdk.services.sts.DefaultStsClient", "method": "assumeRole", "line": 292},
              {"class": "org.apache.polaris.core.storage.aws.AwsCredentialsStorageIntegration", "method": "compute", "line": 251},
              {"class": "org.apache.polaris.core.storage.aws.AwsStorageCredentialCacheKey", "method": "load", "line": 83},
              {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "lambda$new$1", "line": 66},
              {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "lambda$newMappingFunction$0", "line": 192},
              {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "lambda$doComputeIfAbsent$0", "line": 2767},
              {"class": "java.util.concurrent.ConcurrentHashMap", "method": "compute", "line": 1916},
              {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "doComputeIfAbsent", "line": 2765},
              {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "computeIfAbsent", "line": 2756},
              {"class": "com.github.benmanes.caffeine.cache.LocalCache", "method": "computeIfAbsent", "line": 132},
              {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "get", "line": 60},
              {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "getOrLoad", "line": 94},
              {"class": "org.apache.polaris.core.storage.cache.ServiceProducers_ProducerMethod_storageCredentialCache_7RHD-esc0KR78_Ued1hDYZdCCAg_ClientProxy", "method": "getOrLoad"},
              {"class": "org.apache.polaris.core.storage.CachingStorageIntegration", "method": "getStorageAccessConfig", "line": 76},
              {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 135},
              {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 88},
              {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider_ClientProxy", "method": "getStorageAccessConfig"},
              {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog", "method": "loadFileIOForTableLike", "line": 2403},
              {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "doCommit", "line": 1742},
              {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "commit", "line": 1597},
              {"class": "org.apache.iceberg.BaseMetastoreCatalog$BaseMetastoreCatalogTableBuilder", "method": "create", "line": 201},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "createTableDirect", "line": 489},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$createTable$7", "line": 300},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalogByName", "line": 114},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 106},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "createTable", "line": 284},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable$$superforward"},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "createTable"},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "createTable", "line": 323},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable"},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "createTable"},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "createTable", "line": 198},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable$$superforward"},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$2", "method": "apply"},
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
              {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 31},
              {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
              {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
              {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
              {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
              {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 48},
              {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor$RolesAllowedInterceptor_Bean", "method": "intercept"},
              {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
              {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
              {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable"},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$createTable_a10bf5c238b8901b2eb111a115d60b2d128401c9", "method": "invoke"},
              {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
              {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 190},
              {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
              {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 695},
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
      }
    }
  },
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-3201-probe-500-black_hole_endpoint-create_table_0",
    "realmId": "POLARIS"
  },
  "sequence": 5051
}
```

---

## 6. 상세 — requestId 단위 요청 추적

`mdc.requestId` 는 한 요청이 남긴 모든 줄을 묶습니다. 액세스 로그(무엇을 요청했나) + 예외 로그(왜 실패했나) + 관리 로그(무엇이 바뀌었나).

**파이프라인이 이것을 판정에도 씁니다**: 허용 목록 앱 로그는 같은 `requestId` 의 액세스 라인이 올 때까지 보류되고, 그 요청이 404 면 **함께 버려집니다** (`app_dropped_404`). 그래서 상세 인덱스에 남은 앱 로그는 "적재된 요청의 앱 로그" 뿐입니다.

아래는 이 구간에서 가장 많은 줄을 남긴 요청 `nb-1789965827-3203-probe-500-black_hole_endpoint-create_table_2` (3건) 입니다.

#### 6.1 `IcebergExceptionMapper`

```json
{
  "@timestamp": "2026-09-21T04:44:11.495Z",
  "_time": "2026-09-21T04:44:11.493061851Z",
  "level": "ERROR",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Unhandled exception returning INTERNAL_SERVER_ERROR",
  "threadName": "executor-thread-19",
  "threadId": 61,
  "exception": {
    "refId": 1,
    "exceptionType": "software.amazon.awssdk.core.exception.SdkClientException",
    "message": "Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused (SDK Attempt Count: 4)",
    "frames": [
      {"class": "software.amazon.awssdk.core.exception.SdkClientException$BuilderImpl", "method": "build", "line": 130},
      {"class": "software.amazon.awssdk.core.exception.SdkClientException$BuilderImpl", "method": "build", "line": 95},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.utils.RetryableStageHelper", "method": "retryPolicyDisallowedRetryException", "line": 180},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 86},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 39},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
      {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 53},
      {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 35},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "executeWithTimer", "line": 82},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 62},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 43},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 50},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 32},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 37},
      {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 26},
      {"class": "software.amazon.awssdk.core.internal.http.AmazonSyncHttpClient$RequestExecutionBuilderImpl", "method": "execute", "line": 210},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "invoke", "line": 103},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "doExecute", "line": 173},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "lambda$execute$1", "line": 80},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "measureApiCallSuccess", "line": 182},
      {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "execute", "line": 74},
      {"class": "software.amazon.awssdk.core.client.handler.SdkSyncClientHandler", "method": "execute", "line": 45},
      {"class": "software.amazon.awssdk.awscore.client.handler.AwsSyncClientHandler", "method": "execute", "line": 53},
      {"class": "software.amazon.awssdk.services.sts.DefaultStsClient", "method": "assumeRole", "line": 292},
      {"class": "org.apache.polaris.core.storage.aws.AwsCredentialsStorageIntegration", "method": "compute", "line": 251},
      {"class": "org.apache.polaris.core.storage.aws.AwsStorageCredentialCacheKey", "method": "load", "line": 83},
      {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "lambda$new$1", "line": 66},
      {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "lambda$newMappingFunction$0", "line": 192},
      {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "lambda$doComputeIfAbsent$0", "line": 2767},
      {"class": "java.util.concurrent.ConcurrentHashMap", "method": "compute", "line": 1955},
      {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "doComputeIfAbsent", "line": 2765},
      {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "computeIfAbsent", "line": 2756},
      {"class": "com.github.benmanes.caffeine.cache.LocalCache", "method": "computeIfAbsent", "line": 132},
      {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "get", "line": 60},
      {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "getOrLoad", "line": 94},
      {"class": "org.apache.polaris.core.storage.cache.ServiceProducers_ProducerMethod_storageCredentialCache_7RHD-esc0KR78_Ued1hDYZdCCAg_ClientProxy", "method": "getOrLoad"},
      {"class": "org.apache.polaris.core.storage.CachingStorageIntegration", "method": "getStorageAccessConfig", "line": 76},
      {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 135},
      {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 88},
      {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider_ClientProxy", "method": "getStorageAccessConfig"},
      {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog", "method": "loadFileIOForTableLike", "line": 2403},
      {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "doCommit", "line": 1742},
      {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "commit", "line": 1597},
      {"class": "org.apache.iceberg.BaseMetastoreCatalog$BaseMetastoreCatalogTableBuilder", "method": "create", "line": 201},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "createTableDirect", "line": 489},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$createTable$7", "line": 300},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalogByName", "line": 114},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 106},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "createTable", "line": 284},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable$$superforward"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "createTable"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "createTable", "line": 323},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable"},
      {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "createTable"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "createTable", "line": 198},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable$$superforward"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$2", "method": "apply"},
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
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 31},
      {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 48},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor$RolesAllowedInterceptor_Bean", "method": "intercept"},
      {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
      {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
      {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable"},
      {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$createTable_a10bf5c238b8901b2eb111a115d60b2d128401c9", "method": "invoke"},
      {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
      {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 190},
      {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
      {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 695},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
      {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
      {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
      {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
      {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
      {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
      {"class": "java.lang.Thread", "method": "run", "line": 1583}
    ],
    "suppressed": [
      {
        "refId": 2,
        "exceptionType": "software.amazon.awssdk.core.exception.SdkClientException",
        "message": "Request attempt 1 failure: Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused",
        "frames": []
      },
      {
        "refId": 3,
        "exceptionType": "software.amazon.awssdk.core.exception.SdkClientException",
        "message": "Request attempt 2 failure: Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused",
        "frames": []
      },
      {
        "refId": 4,
        "exceptionType": "software.amazon.awssdk.core.exception.SdkClientException",
        "message": "Request attempt 3 failure: Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused",
        "frames": []
      }
    ],
    "causedBy": {
      "exception": {
        "refId": 5,
        "exceptionType": "org.apache.http.conn.HttpHostConnectException",
        "message": "Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused",
        "frames": [
          {"class": "org.apache.http.impl.conn.DefaultHttpClientConnectionOperator", "method": "connect", "line": 156},
          {"class": "org.apache.http.impl.conn.PoolingHttpClientConnectionManager", "method": "connect", "line": 376},
          {"class": "software.amazon.awssdk.http.apache.internal.conn.ClientConnectionManagerFactory$DelegatingHttpClientConnectionManager", "method": "connect", "line": 86},
          {"class": "org.apache.http.impl.execchain.MainClientExec", "method": "establishRoute", "line": 393},
          {"class": "org.apache.http.impl.execchain.MainClientExec", "method": "execute", "line": 236},
          {"class": "org.apache.http.impl.execchain.ProtocolExec", "method": "execute", "line": 186},
          {"class": "org.apache.http.impl.client.InternalHttpClient", "method": "doExecute", "line": 185},
          {"class": "org.apache.http.impl.client.CloseableHttpClient", "method": "execute", "line": 83},
          {"class": "org.apache.http.impl.client.CloseableHttpClient", "method": "execute", "line": 56},
          {"class": "software.amazon.awssdk.http.apache.internal.impl.ApacheSdkHttpClient", "method": "execute", "line": 72},
          {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient", "method": "execute", "line": 261},
          {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient", "method": "access$600", "line": 106},
          {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient$1", "method": "call", "line": 238},
          {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient$1", "method": "call", "line": 235},
          {"class": "software.amazon.awssdk.core.internal.util.MetricUtils", "method": "measureDurationUnsafe", "line": 103},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "executeHttpRequest", "line": 92},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "execute", "line": 68},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "execute", "line": 50},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage", "method": "execute", "line": 74},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage", "method": "execute", "line": 43},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage", "method": "execute", "line": 79},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage", "method": "execute", "line": 41},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage", "method": "execute", "line": 58},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage", "method": "execute", "line": 41},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "executeRequest", "line": 106},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 62},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 39},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 53},
          {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 35},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "executeWithTimer", "line": 82},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 62},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 43},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 50},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 32},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 37},
          {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 26},
          {"class": "software.amazon.awssdk.core.internal.http.AmazonSyncHttpClient$RequestExecutionBuilderImpl", "method": "execute", "line": 210},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "invoke", "line": 103},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "doExecute", "line": 173},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "lambda$execute$1", "line": 80},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "measureApiCallSuccess", "line": 182},
          {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "execute", "line": 74},
          {"class": "software.amazon.awssdk.core.client.handler.SdkSyncClientHandler", "method": "execute", "line": 45},
          {"class": "software.amazon.awssdk.awscore.client.handler.AwsSyncClientHandler", "method": "execute", "line": 53},
          {"class": "software.amazon.awssdk.services.sts.DefaultStsClient", "method": "assumeRole", "line": 292},
          {"class": "org.apache.polaris.core.storage.aws.AwsCredentialsStorageIntegration", "method": "compute", "line": 251},
          {"class": "org.apache.polaris.core.storage.aws.AwsStorageCredentialCacheKey", "method": "load", "line": 83},
          {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "lambda$new$1", "line": 66},
          {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "lambda$newMappingFunction$0", "line": 192},
          {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "lambda$doComputeIfAbsent$0", "line": 2767},
          {"class": "java.util.concurrent.ConcurrentHashMap", "method": "compute", "line": 1955},
          {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "doComputeIfAbsent", "line": 2765},
          {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "computeIfAbsent", "line": 2756},
          {"class": "com.github.benmanes.caffeine.cache.LocalCache", "method": "computeIfAbsent", "line": 132},
          {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "get", "line": 60},
          {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "getOrLoad", "line": 94},
          {"class": "org.apache.polaris.core.storage.cache.ServiceProducers_ProducerMethod_storageCredentialCache_7RHD-esc0KR78_Ued1hDYZdCCAg_ClientProxy", "method": "getOrLoad"},
          {"class": "org.apache.polaris.core.storage.CachingStorageIntegration", "method": "getStorageAccessConfig", "line": 76},
          {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 135},
          {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 88},
          {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider_ClientProxy", "method": "getStorageAccessConfig"},
          {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog", "method": "loadFileIOForTableLike", "line": 2403},
          {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "doCommit", "line": 1742},
          {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "commit", "line": 1597},
          {"class": "org.apache.iceberg.BaseMetastoreCatalog$BaseMetastoreCatalogTableBuilder", "method": "create", "line": 201},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "createTableDirect", "line": 489},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$createTable$7", "line": 300},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalogByName", "line": 114},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 106},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "createTable", "line": 284},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable$$superforward"},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "createTable"},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "createTable", "line": 323},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable"},
          {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "createTable"},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "createTable", "line": 198},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable$$superforward"},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$2", "method": "apply"},
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
          {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 31},
          {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
          {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
          {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
          {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
          {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 48},
          {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor$RolesAllowedInterceptor_Bean", "method": "intercept"},
          {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
          {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
          {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable"},
          {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$createTable_a10bf5c238b8901b2eb111a115d60b2d128401c9", "method": "invoke"},
          {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
          {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 190},
          {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
          {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 695},
          {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "doRunWith", "line": 2651},
          {"class": "org.jboss.threads.EnhancedQueueExecutor$Task", "method": "run", "line": 2630},
          {"class": "org.jboss.threads.EnhancedQueueExecutor", "method": "runThreadBody", "line": 1622},
          {"class": "org.jboss.threads.EnhancedQueueExecutor$ThreadBody", "method": "run", "line": 1589},
          {"class": "org.jboss.threads.DelegatingRunnable", "method": "run", "line": 11},
          {"class": "org.jboss.threads.ThreadLocalResettingRunnable", "method": "run", "line": 11},
          {"class": "io.netty.util.concurrent.FastThreadLocalRunnable", "method": "run", "line": 30},
          {"class": "java.lang.Thread", "method": "run", "line": 1583}
        ],
        "causedBy": {
          "exception": {
            "refId": 6,
            "exceptionType": "java.net.ConnectException",
            "message": "Connection refused",
            "frames": [
              {"class": "sun.nio.ch.Net", "method": "pollConnect"},
              {"class": "sun.nio.ch.Net", "method": "pollConnectNow", "line": 694},
              {"class": "sun.nio.ch.NioSocketImpl", "method": "timedFinishConnect", "line": 542},
              {"class": "sun.nio.ch.NioSocketImpl", "method": "connect", "line": 592},
              {"class": "java.net.SocksSocketImpl", "method": "connect", "line": 327},
              {"class": "java.net.Socket", "method": "connect", "line": 751},
              {"class": "org.apache.http.conn.socket.PlainConnectionSocketFactory", "method": "connectSocket", "line": 75},
              {"class": "org.apache.http.impl.conn.DefaultHttpClientConnectionOperator", "method": "connect", "line": 142},
              {"class": "org.apache.http.impl.conn.PoolingHttpClientConnectionManager", "method": "connect", "line": 376},
              {"class": "software.amazon.awssdk.http.apache.internal.conn.ClientConnectionManagerFactory$DelegatingHttpClientConnectionManager", "method": "connect", "line": 86},
              {"class": "org.apache.http.impl.execchain.MainClientExec", "method": "establishRoute", "line": 393},
              {"class": "org.apache.http.impl.execchain.MainClientExec", "method": "execute", "line": 236},
              {"class": "org.apache.http.impl.execchain.ProtocolExec", "method": "execute", "line": 186},
              {"class": "org.apache.http.impl.client.InternalHttpClient", "method": "doExecute", "line": 185},
              {"class": "org.apache.http.impl.client.CloseableHttpClient", "method": "execute", "line": 83},
              {"class": "org.apache.http.impl.client.CloseableHttpClient", "method": "execute", "line": 56},
              {"class": "software.amazon.awssdk.http.apache.internal.impl.ApacheSdkHttpClient", "method": "execute", "line": 72},
              {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient", "method": "execute", "line": 261},
              {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient", "method": "access$600", "line": 106},
              {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient$1", "method": "call", "line": 238},
              {"class": "software.amazon.awssdk.http.apache.ApacheHttpClient$1", "method": "call", "line": 235},
              {"class": "software.amazon.awssdk.core.internal.util.MetricUtils", "method": "measureDurationUnsafe", "line": 103},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "executeHttpRequest", "line": 92},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "execute", "line": 68},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.MakeHttpRequestStage", "method": "execute", "line": 50},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage", "method": "execute", "line": 74},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage", "method": "execute", "line": 43},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage", "method": "execute", "line": 79},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage", "method": "execute", "line": 41},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage", "method": "execute", "line": 58},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage", "method": "execute", "line": 41},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "executeRequest", "line": 106},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 62},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage", "method": "execute", "line": 39},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 53},
              {"class": "software.amazon.awssdk.core.internal.http.StreamManagingStage", "method": "execute", "line": 35},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "executeWithTimer", "line": 82},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 62},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage", "method": "execute", "line": 43},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 50},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage", "method": "execute", "line": 32},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage", "method": "execute", "line": 206},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 37},
              {"class": "software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage", "method": "execute", "line": 26},
              {"class": "software.amazon.awssdk.core.internal.http.AmazonSyncHttpClient$RequestExecutionBuilderImpl", "method": "execute", "line": 210},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "invoke", "line": 103},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "doExecute", "line": 173},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "lambda$execute$1", "line": 80},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "measureApiCallSuccess", "line": 182},
              {"class": "software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler", "method": "execute", "line": 74},
              {"class": "software.amazon.awssdk.core.client.handler.SdkSyncClientHandler", "method": "execute", "line": 45},
              {"class": "software.amazon.awssdk.awscore.client.handler.AwsSyncClientHandler", "method": "execute", "line": 53},
              {"class": "software.amazon.awssdk.services.sts.DefaultStsClient", "method": "assumeRole", "line": 292},
              {"class": "org.apache.polaris.core.storage.aws.AwsCredentialsStorageIntegration", "method": "compute", "line": 251},
              {"class": "org.apache.polaris.core.storage.aws.AwsStorageCredentialCacheKey", "method": "load", "line": 83},
              {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "lambda$new$1", "line": 66},
              {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "lambda$newMappingFunction$0", "line": 192},
              {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "lambda$doComputeIfAbsent$0", "line": 2767},
              {"class": "java.util.concurrent.ConcurrentHashMap", "method": "compute", "line": 1955},
              {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "doComputeIfAbsent", "line": 2765},
              {"class": "com.github.benmanes.caffeine.cache.BoundedLocalCache", "method": "computeIfAbsent", "line": 2756},
              {"class": "com.github.benmanes.caffeine.cache.LocalCache", "method": "computeIfAbsent", "line": 132},
              {"class": "com.github.benmanes.caffeine.cache.LocalLoadingCache", "method": "get", "line": 60},
              {"class": "org.apache.polaris.core.storage.cache.StorageCredentialCache", "method": "getOrLoad", "line": 94},
              {"class": "org.apache.polaris.core.storage.cache.ServiceProducers_ProducerMethod_storageCredentialCache_7RHD-esc0KR78_Ued1hDYZdCCAg_ClientProxy", "method": "getOrLoad"},
              {"class": "org.apache.polaris.core.storage.CachingStorageIntegration", "method": "getStorageAccessConfig", "line": 76},
              {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 135},
              {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider", "method": "getStorageAccessConfig", "line": 88},
              {"class": "org.apache.polaris.service.catalog.io.StorageAccessConfigProvider_ClientProxy", "method": "getStorageAccessConfig"},
              {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog", "method": "loadFileIOForTableLike", "line": 2403},
              {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "doCommit", "line": 1742},
              {"class": "org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog$BasePolarisTableOperations", "method": "commit", "line": 1597},
              {"class": "org.apache.iceberg.BaseMetastoreCatalog$BaseMetastoreCatalogTableBuilder", "method": "create", "line": 201},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler", "method": "createTableDirect", "line": 489},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "lambda$createTable$7", "line": 300},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalogByName", "line": 114},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "withCatalog", "line": 106},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter", "method": "createTable", "line": 284},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable$$superforward"},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator_Gj_WCptqTcdHu-fbZfgVkAwPXCI_Delegate_Subclass", "method": "createTable"},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergRestCatalogEventServiceDelegator", "method": "createTable", "line": 323},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_Subclass", "method": "createTable"},
              {"class": "org.apache.polaris.service.catalog.iceberg.IcebergCatalogAdapter_ClientProxy", "method": "createTable"},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi", "method": "createTable", "line": 198},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable$$superforward"},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass$2", "method": "apply"},
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
              {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor", "method": "intercept", "line": 31},
              {"class": "io.quarkus.security.runtime.interceptor.RolesAllowedInterceptor_Bean", "method": "intercept"},
              {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
              {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 70},
              {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "proceed", "line": 62},
              {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor", "method": "intercept", "line": 48},
              {"class": "io.quarkus.resteasy.reactive.server.runtime.StandardSecurityCheckInterceptor$RolesAllowedInterceptor_Bean", "method": "intercept"},
              {"class": "io.quarkus.arc.impl.InterceptorInvocation", "method": "invoke", "line": 42},
              {"class": "io.quarkus.arc.impl.AroundInvokeInvocationContext", "method": "perform", "line": 30},
              {"class": "io.quarkus.arc.impl.InvocationContexts", "method": "performAroundInvoke", "line": 27},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi_Subclass", "method": "createTable"},
              {"class": "org.apache.polaris.service.catalog.api.IcebergRestCatalogApi$quarkusrestinvoker$createTable_a10bf5c238b8901b2eb111a115d60b2d128401c9", "method": "invoke"},
              {"class": "org.jboss.resteasy.reactive.server.handlers.InvocationHandler", "method": "handle", "line": 29},
              {"class": "io.quarkus.resteasy.reactive.server.runtime.QuarkusResteasyReactiveRequestContext", "method": "invokeHandler", "line": 190},
              {"class": "org.jboss.resteasy.reactive.common.core.AbstractResteasyReactiveContext", "method": "run", "line": 147},
              {"class": "io.quarkus.vertx.core.runtime.VertxCoreRecorder$15", "method": "runWith", "line": 695},
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
      }
    }
  },
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-3203-probe-500-black_hole_endpoint-create_table_2",
    "realmId": "POLARIS"
  },
  "sequence": 5061
}
```

#### 6.2 `access-log`

```json
{
  "@timestamp": "2026-09-21T04:44:11.497Z",
  "_time": "2026-09-21T04:44:11.495259037Z",
  "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "message": "192.168.194.1 - mx_1789965827_runner [21/Sep/2026:04:44:11 +0000] \"POST /api/catalog/v1/nb1789965827bh/namespaces/bh_ns/tables HTTP/1.1\" 500 180",
  "threadName": "executor-thread-19",
  "threadId": 61,
  "user_principal_name": "mx_1789965827_runner",
  "client_ip": "192.168.194.1",
  "http_method": "POST",
  "api_path": "/api/catalog/v1/nb1789965827bh/namespaces/bh_ns/tables",
  "http_status": 500,
  "response_size": 180,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-3203-probe-500-black_hole_endpoint-create_table_2",
    "realmId": "POLARIS"
  },
  "sequence": 5062
}
```

#### 6.3 `IcebergExceptionMapper`

```json
{
  "@timestamp": "2026-09-21T04:44:11.497Z",
  "_time": "2026-09-21T04:44:11.492809557Z",
  "level": "INFO",
  "loggerName": "org.apache.polaris.service.exception.IcebergExceptionMapper",
  "message": "Handling runtimeException Unable to execute HTTP request: Connect to 127.0.0.1:1 [/127.0.0.1] failed: Connection refused (SDK Attempt Count: 4)",
  "threadName": "executor-thread-19",
  "threadId": 61,
  "hostName": "benchmarks-polaris-c7c64b9dd-cwb8k",
  "mdc": {
    "requestId": "nb-1789965827-3203-probe-500-black_hole_endpoint-create_table_2",
    "realmId": "POLARIS"
  },
  "sequence": 5060
}
```

---

## 7. 요약 — summary

윈도우당 **한 행**. 그 윈도우에서 무슨 일이 있었는지의 전체 수치이고, **적재되지 않은 요청의 유일한 기록**입니다.

`message` 는 사람이 읽는 한 문장이며 v6 에서는 `summary` 행에만 있습니다. `partial_window` 는 **불리언이 아니라 문자열** `"true"`/`"false"` 입니다.

#### 7.1 트래픽이 있던 윈도우 (`2026-09-21T04:44:00Z`)

```json
{
  "@timestamp": "2026-09-21T04:44:33.092Z",
  "_time": "2026-09-21T04:44:30Z",
  "schema_version": 6,
  "report_type": "summary",
  "report_seq": 526,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:44:00Z",
  "window_end": "2026-09-21T04:44:30Z",
  "window_seconds": 30,
  "partial_window": "false",
  "message": "polaris shipper report seq=526@benchmarks-fluent-bit-pdr2h 2026-09-21T04:44:00Z..2026-09-21T04:44:30Z: 356 access lines, 202 kept, 154 counted (36 read, 21 POST, 97 404), 150 errors kept (240 4xx, 7 5xx, 110 denied), 60 resources, 4 principals, 94 app lines dropped, 1071075 bytes, 0 windows skipped",
  "errors_4xx": 240,
  "errors_5xx": 7,
  "auth_denied": 110,
  "access_counted": 154,
  "access_kept": 202,
  "access_seen": 356,
  "app_dropped_404": 107,
  "app_dropped_total": 94,
  "bytes_total": 1071075,
  "counted_404": 97,
  "counted_post": 21,
  "counted_read": 36,
  "distinct_principals": 4,
  "distinct_resources": 60,
  "errors_kept": 150,
  "held_orphans": 0,
  "held_pending": 0,
  "max_record_time": "2026-09-21T04:44:13.070755801Z",
  "min_record_time": "2026-09-21T04:44:06.53671358Z",
  "parse_errors": 0,
  "principals_other": 0,
  "resources_other": 0,
  "resources_other_distinct": 0,
  "role_keys_forced": 4,
  "windows_skipped": 0
}
```

#### 7.2 빈 윈도우 — 이 export 의 28/30 개가 이 모양입니다

```json
{
  "@timestamp": "2026-09-21T04:33:03.095Z",
  "_time": "2026-09-21T04:33:00Z",
  "schema_version": 6,
  "report_type": "summary",
  "report_seq": 503,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:32:30Z",
  "window_end": "2026-09-21T04:33:00Z",
  "window_seconds": 30,
  "partial_window": "false",
  "message": "polaris shipper report seq=503@benchmarks-fluent-bit-pdr2h 2026-09-21T04:32:30Z..2026-09-21T04:33:00Z: 0 access lines, 0 kept, 0 counted (0 read, 0 POST, 0 404), 0 errors kept (0 4xx, 0 5xx, 0 denied), 0 resources, 0 principals, 0 app lines dropped, 0 bytes, 0 windows skipped",
  "errors_4xx": 0,
  "errors_5xx": 0,
  "auth_denied": 0,
  "access_counted": 0,
  "access_kept": 0,
  "access_seen": 0,
  "app_dropped_404": 0,
  "app_dropped_total": 0,
  "bytes_total": 0,
  "counted_404": 0,
  "counted_post": 0,
  "counted_read": 0,
  "distinct_principals": 0,
  "distinct_resources": 0,
  "errors_kept": 0,
  "held_orphans": 0,
  "held_pending": 0,
  "parse_errors": 0,
  "principals_other": 0,
  "resources_other": 0,
  "resources_other_distinct": 0,
  "role_keys_forced": 0,
  "windows_skipped": 0
}
```

---

## 8. 요약 — principal

`user_principal_name` 별 한 행. **누가** 얼마나 요청했고 얼마나 거부당했는지. `-` 는 미인증/인증 실패입니다.

#### 8.1 `mx_1789965827_runner` — 109 requests, 1 denied

```json
{
  "@timestamp": "2026-09-21T04:44:33.092Z",
  "_time": "2026-09-21T04:44:30Z",
  "schema_version": 6,
  "report_type": "principal",
  "report_seq": 526,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:44:00Z",
  "window_end": "2026-09-21T04:44:30Z",
  "window_seconds": 30,
  "user_principal_name": "mx_1789965827_runner",
  "requests": 109,
  "reads": 29,
  "writes": 80,
  "errors": 55,
  "errors_4xx": 49,
  "errors_5xx": 6,
  "auth_denied": 1,
  "response_bytes": 27524
}
```

#### 8.2 `root` — 102 requests, 1 denied

```json
{
  "@timestamp": "2026-09-21T04:44:33.092Z",
  "_time": "2026-09-21T04:44:30Z",
  "schema_version": 6,
  "report_type": "principal",
  "report_seq": 526,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:44:00Z",
  "window_end": "2026-09-21T04:44:30Z",
  "window_seconds": 30,
  "user_principal_name": "root",
  "requests": 102,
  "reads": 27,
  "writes": 75,
  "errors": 49,
  "errors_4xx": 49,
  "errors_5xx": 0,
  "auth_denied": 1,
  "response_bytes": 1024943
}
```

#### 8.3 `-` — 85 requests, 60 denied

```json
{
  "@timestamp": "2026-09-21T04:44:33.092Z",
  "_time": "2026-09-21T04:44:30Z",
  "schema_version": 6,
  "report_type": "principal",
  "report_seq": 526,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:44:00Z",
  "window_end": "2026-09-21T04:44:30Z",
  "window_seconds": 30,
  "user_principal_name": "-",
  "requests": 85,
  "reads": 28,
  "writes": 57,
  "errors": 84,
  "errors_4xx": 83,
  "errors_5xx": 1,
  "auth_denied": 60,
  "response_bytes": 3466
}
```

#### 8.4 `root` — 82 requests, 0 denied

```json
{
  "@timestamp": "2026-09-21T04:44:03.095Z",
  "_time": "2026-09-21T04:44:00Z",
  "schema_version": 6,
  "report_type": "principal",
  "report_seq": 525,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:43:30Z",
  "window_end": "2026-09-21T04:44:00Z",
  "window_seconds": 30,
  "user_principal_name": "root",
  "requests": 82,
  "reads": 30,
  "writes": 52,
  "errors": 2,
  "errors_4xx": 2,
  "errors_5xx": 0,
  "auth_denied": 0,
  "response_bytes": 26314
}
```

---

## 9. 요약 — resource

리소스(경로) 별 한 행. **무엇이** 얼마나 불렸고 얼마나 실패했는지.

세 가지 특수 행을 알아두면 읽기 쉽습니다:

| 행 | 뜻 |
|---|---|
| `__errors__` | **오류 요청은 새 리소스 행을 만들지 못합니다** (`create=false` — 없는 테이블 이름을 두드리는 클라이언트가 키 공간을 채우지 못하게). 같은 윈도우에서 그 경로의 성공 요청이 먼저 오지 않았다면, 오류는 전부 이 한 행으로 모입니다. **개수는 보존되고 귀속만 사라집니다** |
| `__other__` | 리소스 행이 상한(500)을 넘겼을 때 넘친 요청이 모이는 행. 이 export 에는 없습니다 |
| 롤 행 (`catalog-role` / `principal-role`) | 예외적으로 **오류로도 행을 만듭니다** — 거부된 grant 가 곧 롤 행이 답해야 할 보안 질문이기 때문. 상한은 별도(100), 넘긴 개수는 `summary.role_keys_forced` |

#### 9.1 일반 리소스 행 — `/api/management/v1/catalogs/apimatrix1789965827_cat/catalog-roles/apimatrix1789965827_shared`

```json
{
  "@timestamp": "2026-09-21T04:44:03.095Z",
  "_time": "2026-09-21T04:44:00Z",
  "schema_version": 6,
  "report_type": "resource",
  "report_seq": 525,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:43:30Z",
  "window_end": "2026-09-21T04:44:00Z",
  "window_seconds": 30,
  "resource": "/api/management/v1/catalogs/apimatrix1789965827_cat/catalog-roles/apimatrix1789965827_shared",
  "resource_kind": "catalog-role",
  "api_kind": "management",
  "requests": 50,
  "reads": 25,
  "writes": 25,
  "errors": 0,
  "errors_4xx": 0,
  "errors_5xx": 0,
  "auth_denied": 0,
  "response_bytes": 16205,
  "last_read_bytes": 1254
}
```

#### 9.2 롤 행 — 거부된 요청이 만든 행 — `/api/management/v1/principal-roles/mx_1789965827_prole_doomed`

```json
{
  "@timestamp": "2026-09-21T04:44:33.092Z",
  "_time": "2026-09-21T04:44:30Z",
  "schema_version": 6,
  "report_type": "resource",
  "report_seq": 526,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:44:00Z",
  "window_end": "2026-09-21T04:44:30Z",
  "window_seconds": 30,
  "resource": "/api/management/v1/principal-roles/mx_1789965827_prole_doomed",
  "resource_kind": "principal-role",
  "api_kind": "management",
  "requests": 8,
  "reads": 0,
  "writes": 8,
  "errors": 7,
  "errors_4xx": 7,
  "errors_5xx": 0,
  "auth_denied": 2,
  "response_bytes": 905
}
```

#### 9.3 `__errors__` — 귀속되지 못한 오류 — `__errors__`

```json
{
  "@timestamp": "2026-09-21T04:44:03.095Z",
  "_time": "2026-09-21T04:44:00Z",
  "schema_version": 6,
  "report_type": "resource",
  "report_seq": 525,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:43:30Z",
  "window_end": "2026-09-21T04:44:00Z",
  "window_seconds": 30,
  "resource": "__errors__",
  "resource_kind": "error",
  "api_kind": "mixed",
  "requests": 2,
  "reads": 2,
  "writes": 0,
  "errors": 2,
  "errors_4xx": 2,
  "errors_5xx": 0,
  "auth_denied": 0,
  "response_bytes": 264
}
```

---

## 10. 요약 — app_dropped

허용 목록(`APP_ALLOW`) 밖이라 **버린** 애플리케이션 로그를, logger 별로 몇 줄 버렸는지만 남깁니다. 추이 지표가 아니라 **헬스 신호**입니다: 여기에 새 `org.apache.polaris.service.*` 가 보이면 허용 목록을 검토하라는 뜻입니다.

이 export 의 버린 줄 합계는 124건입니다.

| logger | 버린 줄 |
|---|---|
| `org.apache.iceberg.CatalogUtil` | 43 |
| `org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog` | 42 |
| `org.apache.iceberg.BaseMetastoreCatalog` | 30 |
| `org.apache.iceberg.view.BaseMetastoreViewCatalog` | 9 |

#### 10.1 행 하나의 모양

```json
{
  "@timestamp": "2026-09-21T04:44:33.092Z",
  "_time": "2026-09-21T04:44:30Z",
  "schema_version": 6,
  "report_type": "app_dropped",
  "report_seq": 526,
  "hostname": "benchmarks-fluent-bit-pdr2h",
  "window_start": "2026-09-21T04:44:00Z",
  "window_end": "2026-09-21T04:44:30Z",
  "window_seconds": 30,
  "logger_name": "org.apache.iceberg.CatalogUtil",
  "dropped": 34
}
```

---

## 11. 검색 쿼리 예시 (DQL)

> **문자열 필드는 `.keyword` 로 검색합니다.** v6 인덱스 템플릿부터 선언되지 않은 문자열은 `.keyword` 에만 색인되고, 필드명만 쓰면 새 인덱스에서 0건이 나옵니다. `.keyword` 는 이전 인덱스에도 있으므로 아래 쿼리는 전 기간에 그대로 동작합니다. 숫자·`message`(전문 검색) 는 필드명 그대로 씁니다.
>
> **`threadName` 이 특히 함정입니다** — 2026-09-18 에 복원됐지만 명시적 매핑이 없어서 `text`(index:false) + `.keyword` 입니다. `threadName:"executor-thread-16"` 은 **항상 0건**입니다. `threadId` 는 `long` 이라 그대로 씁니다.

```text
# 상세 — polaris-logs-*
loggerName.keyword:"io.quarkus.http.access-log"
loggerName.keyword:"io.quarkus.http.access-log" and http_status >= 500
http_status:401 or http_status:403
user_principal_name.keyword:"root"
level.keyword:"ERROR" and exception.exceptionType.keyword:*
mdc.requestId.keyword:"nb-1789965827-2009-registerTable-2"
loggerName.keyword:"org.apache.polaris.service.admin.PolarisServiceImpl"
threadName.keyword:"executor-thread-16"          # 맨 이름으로 쓰면 0건
threadId:57
message:"Adding grant"
secret_redacted:true
access_log_parse_error:true

# 요약 — polaris-report-*
report_type.keyword:"summary"
report_type.keyword:"summary" and (errors_5xx > 0 or auth_denied > 0 or counted_404 > 0)
report_type.keyword:"principal" and window_start.keyword:"2026-09-21T04:44:00Z"
report_type.keyword:"resource" and errors_5xx > 0
report_type.keyword:"resource" and resource.keyword:"__errors__"
report_type.keyword:"resource" and commit_count > 0
report_type.keyword:"app_dropped"
report_type.keyword:"summary" and partial_window.keyword:"true"
```

**조사 순서**: `report_type:summary` 로 이상 윈도우 발견 (`errors_5xx`, `auth_denied`, `counted_404` 급증) → 같은 `window_start` 의 `principal` / `resource` 행으로 범위 좁히기 → 그 시간대 상세 인덱스에서 실패 요청 찾기 → `mdc.requestId` 로 예외 · 스택 트레이스 · 서비스 로그 확인. 성공한 조회와 404 는 상세 인덱스에 없으므로 **요약 행의 숫자가 그 요청들의 유일한 기록**입니다.

**5xx 를 조사할 때 하나 더**: `resource` 행에 5xx 가 안 보이는데 `summary.errors_5xx` 는 0 이 아닐 수 있습니다. 그 오류는 `__errors__` 행에 있습니다 (§9) — 같은 윈도우에 그 경로의 성공 요청이 없었다는 뜻입니다.

---

*생성: `step14-sample-doc.py polaris-logs.json polaris-summary.json` · 상세 391건 / 요약 122건 · 스키마 v6*
