# Polaris Audit Log 적재

**목적** — Polaris 의 장애 대응 및 감사를 위해, 현재 5일간 보관 중인 로그를 더 긴 기간 보관할 수 있는
정책을 수립한다.

**결정 사항** — 상세 로그와 요약 로그를 **하나의 신규 인덱스에 함께 적재하고, 보관 기간은 30일**로 한다.
(현재 대비 6배. 근거와 대안은 §6, §7 참조.)

| 항목 | 값 |
|---|---|
| 대상 | Polaris (`benchmarks-polaris`, namespace `datahub-hynix`) |
| 신규 인덱스 | `polaris-audit-YYYY.MM.DD` (일 단위) |
| 보관 기간 | **30일** (ISM `hot -> delete`) |
| 적재 방식 | Fluent Bit DaemonSet + Lua 필터 -> OpenSearch 3.5.0 |
| 요약 주기 | 30분 (`WINDOW_SECONDS`, 조정 가능) |
| 문서 상태 | 제안 — 적용 전. 검증 계획은 §9 |

---

## 1. 현황과 문제

OpenSearch 에서는 다른 모든 서비스의 로그를 `kube-fb` Index 에 적재하고 있으며, 해당 인덱스는 용량이 커
적재 기간을 더 늘리기는 어렵다. 즉 **보관 기간은 인덱스 단위로 결정되는데, Polaris 만 길게 두고 싶어도
같은 인덱스에 묶여 있어 불가능한 상태**이다.

| 문제 | 영향 |
|---|---|
| 보관 5일 | 5일이 지난 장애는 로그 자체가 남아 있지 않아 원인 추적 불가 |
| 전 서비스 공용 인덱스 | Polaris 만 보관 기간을 늘릴 수 없음 |
| 전량 적재 | 성공한 조회 요청(2xx GET)이 용량의 대부분을 차지, 감사 가치는 낮음 |

따라서 Polaris 의 로그를 적재하는 Index 를 새로 생성하고, Polaris 의 모든 로그를 저장하는 것이 아닌
**장애 발생 시의 로그와, 현재 활동의 요약만을 기록 및 적재**한다.

---

## 2. 설계 요약

```
Polaris Pod (stdout)
   └─ Fluent Bit DaemonSet  ──▶ [Lua 필터: polaris_noise_filter]
                                   ├─ 적재 판정 (규칙 1~7, §4.5)  ──▶ 상세 문서
                                   └─ 30분 윈도우 집계             ──▶ 요약 문서
                                                                       │
                                                          OpenSearch  polaris-audit-*  (30일)
```

핵심은 **버리는 것이 아니라 세는 것**이다. 적재하지 않기로 판정된 요청도 요약 문서의 카운터에는 반드시
반영되므로, "기록이 없다 = 요청이 없었다" 가 아니라 "기록이 없다 = 요약에서 집계되었다" 가 된다.
총량은 언제나 보존된다.

---

## 3. 적재 로그

### 3.1 [Info] Access Log (HTTP Status 4xx / 5xx)

Info 레벨이지만 클라이언트의 리소스 접근에 대한 시점 및 장애 원인을 파악할 수 있다. 2xx 성공 케이스에
대한 로그는 요약 로그만 적재한다.

```
192.168.194.1 - root [14/Sep/2026:07:29:31 +0000] "PUT /api/management/v1/catalogs/nb1789370776stale HTTP/1.1" 409 132
```

```
192.168.194.1 - root [14/Sep/2026:07:29:31 +0000] "DELETE /api/management/v1/principals/mx_1789370776_p_doomed HTTP/1.1" 404 133
```

404 의 경우에는 모니터링 중 발생 횟수가 많은 경우에는 요약 로그로 변환한다.

```
192.168.194.1 - mx_1789370776_runner [14/Sep/2026:07:27:30 +0000] "POST /api/catalog/v1/apimatrix1789370776_cat/views/rename HTTP/1.1" 500 168
```

액세스 라인은 적재 시 다음 필드로 파싱되어 저장되므로, 원문 문자열 검색 없이 조건 검색이 가능하다.

| 필드 | 예시 | 용도 |
|---|---|---|
| `client_ip` | `192.168.194.1` | 호출 출처 |
| `user_principal_name` | `root`, `-` | 호출 주체. **`-` 는 미인증 또는 인증 실패**이며 결측이 아니다 |
| `http_method` | `PUT` | 읽기/쓰기 구분 |
| `api_path` | `/api/management/v1/catalogs/...` | 원본 경로(쿼리스트링 포함) |
| `http_status` | `409` | 숫자형. 범위 검색 가능 |
| `response_size` | `132` | 숫자형. CLF 의 `-` 는 0 으로 저장 |
| `access_log_parse_error` | `true` | 파싱 실패 시에만 존재. **패턴 변경 감지용** |

### 3.2 [Info] Runtime Exception Handling

```
Handling runtimeException TopLevelEntity of type PRINCIPAL_ROLE does not exist: mx_1789370776_prole_doomed
```

Polaris Iceberg Request 의 에러에 대한 원인을 파악할 수 있는 로그이다. 액세스 로그가 *무엇이 실패했는지*
를 알려준다면 이 로그는 *왜 실패했는지* 를 알려주므로, 4xx/5xx 액세스 라인과 **같은 초 단위 시각으로
짝을 이루어** 조회한다.

### 3.3 [Info] Role / Privilege 생성 / 부여

```
Adding grant class AddGrantRequest {
    grant: class CatalogGrant {
        class GrantResource {
            type: catalog
        }
        privilege: TABLE_READ_DATA
    }
} to catalogRole mx_1789370776_crole in catalog apimatrix1789370776_cat
```

리소스에 대한 권한 부여 여부를 추적할 수 있다. 이 로그는 **여러 줄에 걸쳐 출력**되므로 수집 단계에서
multiline 병합이 적용되어야 하며, 병합이 깨지면 한 건의 권한 부여가 여러 문서로 쪼개진다(§10 참조).

### 3.4 WARN / ERROR

WARN / ERROR 레벨은 기본적으로 전부 적재한다. `[WARN] deprecated config` 만 제외한다.

> **참고** — 현재 `polaris/values.yaml` 에서 `io.quarkus.config: "OFF"` 로 설정되어 있어 해당 경고는
> 애초에 출력되지 않는다. 2026-09-04 커버리지 측정(122건 호출)에서도 해당 로그는 0건이었다. 즉 제외
> 규칙은 **방어적 조항**이며, 설정이 되돌려질 경우를 대비해 명시적으로 남긴다.

### 3.5 적재 판정 규칙 (전체)

위 예시들이 실제로 어떤 순서로 판정되는지에 대한 확정 규칙이다. **먼저 일치하는 규칙이 이긴다.**

| 순서 | 조건 | 처리 |
|---|---|---|
| 1 | level 이 `ERROR` 또는 `WARN` | **적재** |
| 2 | 액세스 로그가 아닌 레코드 | **적재** (애플리케이션 로그) |
| — | *여기서 모든 액세스 라인이 요약에 집계된다 — 판정보다 먼저* | |
| 3 | `http_status >= 400` 또는 파싱 실패 | **적재 — 전건, 상한 없음** |
| 4 | `PUT` / `DELETE` / `PATCH` | **적재 — 전건** |
| 5 | `/api/management/` 하위의 `POST` | **적재 — 전건** |
| 5' | 그 외 경로의 `POST` | 집계만 |
| 6 | `GET` / `HEAD` 이고 2xx | 집계만 |
| 7 | 그 외 | 적재 |

이 규칙이 보장하는 것은 두 가지다.

- **인증/인가 실패 100% 보존** — 모든 401·403 은 규칙 3에 의해 전문(全文) 문서로 남는다.
- **신원·권한 변경 100% 보존** — management POST, 모든 PUT, 모든 DELETE.

규칙 5의 management/catalog 분리는 임의 구분이 아니다. Polaris 에서 **POST 는 생성 동사**이며
`create_principal`, `create_principal_role`, `create_catalog_role`, `reset_principal_credentials`
가 모두 POST 이다. POST 를 일괄 집계 처리하면 **principal 이 생성될 때는 보이지 않고 삭제될 때만 보이는**
감사 비대칭이 생긴다. 반대로 catalog POST(`create_table`, `commit_table`, rename, `report_metrics`,
`oauth/tokens`)는 데이터 플레인 트래픽이므로 집계 대상이다.

### 3.6 미적재(제외) 대상

문서가 남지 않는 대상을 명시한다. 모두 **요약 카운터에는 반영**된다.

| 대상 | 이유 | 대체 수단 |
|---|---|---|
| 2xx `GET`/`HEAD` | 정상 조회. 감사 가치 대비 압도적 다수 | `reads`, `last_read_bytes` |
| 2xx catalog `POST` (`create_table`, `commit_table`, `report_metrics`, `oauth/tokens`) | 데이터 플레인 반복 트래픽 | `writes`, `counted_post`, `last_write_bytes` |
| `[WARN] deprecated config` | 설정 경고, 운영 의미 없음 | — |
| DEBUG 레벨 SQL 로그 | 용량의 실질적 다수 | **현재 미분리 — §10 참조** |

---

## 4. 로그 요약

요약은 30분(조정 가능) 단위로 전송하며, 해당 기간 동안 발생한 로그를 취합하여 전송한다. 같은 요청이
중복으로 들어오더라도 해당 요청이 전부 로그로 남는 것이 아니라, 요약 로그 한 줄만 남기기 때문에 로그
적재 시 차지하는 용량을 줄일 수 있다.

> 예) 30분 간 A 테이블에 대한 요청 1000건, 500 reads, 500 writes, 10 errors

요약 문서는 세 가지 종류(`report_type`)가 **같은 윈도우 식별자(`window_start`)를 공유**하므로,
`window_start` 로 묶으면 한 윈도우 전체가 하나의 화면이 된다.

### 4.1 전체 요청 요약 (`report_type: summary`)

```
polaris shipper report seq=191@benchmarks-fluent-bit-d94qc 2026-09-14T07:29:00Z..2026-09-14T07:29:30Z: 53 access lines, 46 kept, 7 counted (4 read, 3 POST), 25 errors kept (25 4xx, 0 5xx, 0 denied), 27 resources, 2 principals, 1 carried, 7847 bytes, 0 windows skipped
```

측정된 기간(30분) 동안 발생한 요청 및 에러의 총 합이다. 윈도우당 정확히 1건.

### 4.2 Resource Request (`report_type: resource`)

```
seq=187 resource /api/catalog/v1/apimatrix1789370776_cat/transactions/commit (catalog/transaction): 2 requests, 0 reads, 2 writes, 1 errors (1 4xx, 0 5xx, 0 denied), 110 bytes
```

API Path 를 Key 로, 해당 리소스에 대한 요청이 몇 건, 그리고 요청 중 에러가 몇 건 발생했는지를 요약하여
전송한다. 테이블 이외에도 모든 리소스(카탈로그, 네임스페이스, 롤 등)에 대한 성공/실패 요청을 요약한다.

키는 **URL 이 아니라 리소스**이다. `/namespaces/ns/tables/t/metrics` 와 `/namespaces/ns/tables/t` 는
같은 테이블이므로 한 행으로 합쳐진다. `resource_kind` 로 분류되며 값은
`table` / `view` / `collection` / `namespace` / `auth` / `config` / `transaction` / `error` / `other`
이고, API 면(面)은 별도 필드 `api_kind`(`catalog` / `management` / `mixed`)로 분리된다.

**권한 부여는 롤 행에 접힌다.** `/catalogs/{cat}/catalog-roles/{cr}/grants` 는
`/catalogs/{cat}/catalog-roles/{cr}` 로 키가 잡히므로, **그 행의 `writes` 가 곧 해당 윈도우에서 부여된
권한 수**이다. §3.3 의 grant 로그와 교차 검증할 수 있다.

### 4.3 Principal Request (`report_type: principal`)

```
seq=185 principal mx_1789370776_runner: 27 requests, 13 reads, 14 writes, 4 errors (4 4xx, 0 5xx, 0 denied), 188475 bytes
```

해당 클라이언트의 요청에 대한 요약 로그이다. 각 클라이언트별 요청이 비정상적으로 높은 경우와 해당
클라이언트의 트래픽 추이를 추적한다.

### 4.4 요약 스키마 필드 정의

공통 봉투(envelope) — 세 종류 모두에 존재한다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `app` | string | `polaris-shipper-report` |
| `level` | string | 항상 `REPORT`. **심각도가 아니라 스트림 선택자** |
| `schema_version` | int | 현재 3. **항상 필터에 포함할 것** — 버전이 공존한다 |
| `report_type` | string | `summary` / `resource` / `principal` |
| `report_seq` | int | **파드 단위 일련번호.** 파드 교체 시 리셋되므로 `hostname` 과 반드시 함께 사용 |
| `hostname` | string | Fluent Bit 파드명 (Polaris 파드가 아님) |
| `window_start` / `window_end` | date | RFC3339. 윈도우 그리드에 정렬 |
| `window_seconds` | int | 30(검증 구간) / 1800(정상 운영) |

`summary` 주요 필드.

| 필드 | 의미 |
|---|---|
| `access_seen` | 필터가 **본** 액세스 라인 수 (판정 이전) |
| `access_kept` | 개별 문서로 적재된 수 |
| `access_counted` | 집계만 되고 적재되지 않은 수 |
| `counted_read` / `counted_post` | 집계분의 규칙 6 / 규칙 5 분해 |
| `errors_kept`, `errors_4xx`, `errors_5xx`, `auth_denied` | 오류 계열 카운터 |
| `parse_errors` | 액세스 로그로 인식됐으나 파싱 실패 |
| `distinct_resources` / `distinct_principals` | **활성(요청>0)** 행 수만 |
| `carried_rows` | 이번 윈도우에 요청이 0이 된 행 수 |
| `resources_other` / `resources_other_distinct` / `principals_other` | 상한(500 / 200) 초과분 |
| `role_keys_forced` | 오류 요청이 강제 생성한 롤 행 수. 100이면 상한 도달 |
| `windows_skipped` | 틱 누락으로 열리지 못한 윈도우 수 |
| `min_record_time` / `max_record_time` | 해당 윈도우 레코드의 최소/최대 시각 |

`resource` / `principal` 행 필드.

| 필드 | 의미 |
|---|---|
| `resource` (또는 `user_principal_name`) | 집계 키 |
| `resource_kind`, `api_kind` | 분류 (principal 행에는 `resource_kind` 없음) |
| `requests`, `reads`, `writes`, `errors` | reads=GET·HEAD, writes=POST·PUT·DELETE·PATCH, errors=status≥400 |
| `errors_4xx`, `errors_5xx`, `auth_denied` | 오류 분해 |
| `response_bytes` | 윈도우 **합계** |
| `last_read_bytes` / `last_write_bytes` | 윈도우 내 마지막 2xx 이고 크기>0 인 읽기/쓰기의 바이트. **없으면 필드 자체가 없음 — 0이 아님** |

### 4.5 요약 해석 시 주의 (대시보드 작성 전 필독)

1. **카운터는 의도적으로 겹친다.** `errors` 는 `reads`/`writes` 와 겹치고, `errors_4xx + errors_5xx` 는
   `errors` 와 겹치며, `auth_denied`(401·403)는 `errors_4xx` 의 **부분집합**이다. 이 컬럼들을 더하는
   대시보드는 틀린다. — 2026-09-14 실측으로 확인: 한 윈도우에서 `auth_denied` 101 = 401 59건 + 403 42건,
   `errors_4xx` 177 에 포함.
2. **부재는 0이 아니다.** `last_write_bytes` 가 없다는 것은 "쓰기 0바이트"가 아니라 "해당 윈도우에 크기
   있는 성공 쓰기가 없었다"이다.
3. **`-` 는 실재하는 주체다.** `user_principal_name: "-"` 는 미인증/인증실패 트래픽이며 결측이 아니다.
4. **`__errors__` 와 `__other__` 는 서로 다르다.** `__errors__` 는 같은 윈도우에 성공 요청이 없었던
   리소스의 오류가 모이는 곳(귀속 정보 소실), `__other__` 는 상한 초과분이다. 단 **그 오류의 원본 문서는
   규칙 3에 의해 전건 보존**되므로 상세에서 복구할 수 있다.
5. **`report_seq` 는 파드 단위**이므로 `hostname` 없이 연속성을 판단하면 안 된다.

---

## 5. 인덱스 설계

### 5.1 인덱스

| 항목 | 값 | 비고 |
|---|---|---|
| 이름 | `polaris-audit-YYYY.MM.DD` | 일 단위 신규 인덱스 |
| 조회 패턴 | `polaris-audit-*` | 대시보드·쿼리는 항상 이 패턴 |
| 상세/요약 | **동일 인덱스** | `level: REPORT` 또는 `report_type` 존재 여부로 구분 |
| shard / replica | 1 / 0 | 단일 노드. 다중 노드 전환 시 replica 1 로 상향 |
| 보관 | **30일** | ISM `hot -> delete` |

### 5.2 인덱스 템플릿은 선택이 아니라 필수

상세와 요약을 한 인덱스에 담기로 한 이상, **동적 매핑에 맡기면 안 된다.** 두 문서 형태의 필드가 한
매핑을 공유하므로, 그 인덱스에 **처음 들어온 문서 한 건이 해당 필드 타입을 그 인덱스의 수명 내내
확정**한다. 실제로 이 파이프라인에서 이미 발생한 사고다 — `polaris-report-2026.09.10` 에서
`min_record_time` 이 `text` 로 굳어 날짜 범위 쿼리와 date histogram 이 영구히 불가능해졌다.

템플릿에서 최소한 다음을 명시한다.

- `window_start`, `window_end`, `min_record_time`, `max_record_time` -> `date`
- 모든 숫자 카운터(`requests`, `reads`, `writes`, `errors`, `errors_4xx`, `errors_5xx`,
  `auth_denied`, `response_bytes`, `http_status`, `response_size`, `last_read_bytes`,
  `last_write_bytes`, …) -> `long`
- 키 필드(`resource`, `user_principal_name`, `api_path`, `resource_kind`, `api_kind`) -> `keyword`
  (또는 `text` + `.keyword`)
- 두 날짜 필드에 `ignore_malformed: true` — 값 하나를 잃을지언정 문서 전체가 거부되지 않게 한다

> **`term` 쿼리는 반드시 `keyword` 필드에 걸 것.** `text` 필드에 `term` 을 걸면 분석기 출력과 비교되어
> 대소문자만으로도 매치가 사라진다(`"POST"` 는 `post` 를 찾지 못한다). 이 경우 쿼리는 **0건을 반환하고
> 조용히 성공**하므로, 검증 게이트가 통과한 것처럼 보인다.

### 5.3 보관 정책 (ISM)

```
hot (rollover: 1d 또는 크기 기준) ──▶ delete (min_index_age: 30d)
```

- 상세·요약 모두 30일 후 삭제
- `kube-fb` 는 변경하지 않는다. Polaris 로그는 신규 인덱스로만 이관되며, 기존 인덱스 정책은 무관

> **repo 기존 계획과의 차이** — `PLAN-opensearch-cutover-2026-09-08.md` §6 은 `polaris-logs-*` 30일 /
> `polaris-report-*` 365일의 **2-인덱스** 구성을 전제한다. 본 문서는 운영 단순화를 위해 **단일 인덱스
> 30일**로 결정했으며, 해당 계획 항목은 본 문서로 대체된다.

### 5.4 단일 인덱스 30일의 트레이드오프

정직하게 밝혀둘 점은, 요약 로그의 가치는 **장기 추이**에 있다는 것이다. 30일은 분기·연간 감사에는
미치지 못한다. 다만 요약은 용량이 매우 작으므로, 필요해지면 **요약만 별도 인덱스로 분리해 1년 보관**하는
확장이 저렴하다.

| 구성 | 추가 용량 | 비고 |
|---|---|---|
| 요약 30일 (현 결정) | 약 **50 MB** | 단순, 단일 정책 |
| 요약만 1년 분리 | 약 **0.6 GB/년** | 분기·연간 감사 가능. 인덱스·정책 2개 관리 |

즉 나중에 되돌릴 수 있는 결정이며, 지금 단일 인덱스로 시작하는 것이 불합리하지 않다.

---

## 6. 용량 추정

### 6.1 산식

| 구분 | 일일 문서 수 |
|---|---|
| 액세스 상세 | 일 요청 수 × (4xx·5xx 비율 + 쓰기 비율) |
| 애플리케이션 상세 | WARN/ERROR 라인 수 |
| 요약 | (86,400 ÷ `window_seconds`) × (1 + 활성 리소스 수 + 활성 principal 수) |

30분 윈도우면 하루 48 윈도우이므로, 활성 리소스 50 + principal 10 기준
`48 × 61 ≈ 2,900건/일` 이다. (30초 윈도우로 운영하면 같은 내용이 약 138,000건/일로 부풀어 오른다 —
검증 구간이 끝나면 1800초로 되돌려야 하는 이유다.)

문서 평균 크기는 원문 + 파싱 필드 + 인덱싱 오버헤드를 포함해 **액세스 1.0 KB / 애플리케이션 1.5 KB /
요약 0.7 KB** 로 가정한다. (**추정치** — 실측으로 대체할 것, §9)

### 6.2 시나리오

| 시나리오 | 일 요청 | 오류율 | 쓰기율 | 적재 문서/일 | 용량/일 | **30일** |
|---|---|---|---|---|---|---|
| A. 현재 로컬 | 수천 | — | — | 수천 | 수 MB | **< 1 GB** |
| B. 소규모 운영 | 1,000,000 | 0.5% | 2% | 약 32,000 | 약 40 MB | **약 1.2 GB** |
| C. 스펙 정상치 | 10,000,000 | 0.5% | 2% | 약 302,000 | 약 380 MB | **약 11 GB** |

비교 — **필터 없이 전량 적재할 경우** 시나리오 C 는 하루 약 10 GB, 30일 **약 300 GB** 가 된다.
본 설계는 같은 기간을 **약 11 GB** 로 보관한다. 이것이 "5일 → 30일"을 가능하게 하는 근거다.

### 6.3 이 추정의 한계

- 시나리오 B·C 의 오류율·쓰기율은 **가정**이다. 실제 Polaris 트래픽은 테이블 메타데이터 폴링(GET)이
  압도적이라 쓰기율은 더 낮을 가능성이 크다 — 즉 **추정이 보수적(과대)** 이다.
- 2026-09-14 커버리지 측정(액세스 433줄 중 343줄 적재, 오류 비중 74%)은 **오류 경로를 일부러 때리는
  테스트**이므로 운영 트래픽 프로파일이 아니다. 용량 산정 근거로 쓸 수 없다.
- **애플리케이션 로그 쪽이 실제 용량의 다수**다(2026-09-04 측정: 122건 호출 → 2,026건 레코드 중
  1,928건이 애플리케이션 라인). 현재 필터는 액세스 스트림만 줄이고 애플리케이션 스트림은 줄이지 않는다.
  §10 의 최우선 미해결 항목.

---

## 7. 활용 시나리오

### 7.1 장애 대응 — "10시경 카탈로그 쓰기가 실패했다"

1. **요약에서 구간 특정** — `report_type: summary` 를 시간순으로 보고 `errors_5xx > 0` 인 윈도우를 찾는다.
2. **리소스 특정** — 같은 `window_start` 의 `report_type: resource` 에서 `errors_5xx > 0` 인 행을 본다.
   어느 테이블·카탈로그인지 여기서 나온다.
3. **상세 조회** — 해당 윈도우 시각 범위 + `http_status >= 500` 으로 액세스 문서 전건을 본다(규칙 3에 의해
   반드시 남아 있다).
4. **원인 확인** — 같은 초의 `Handling runtimeException ...` 및 ERROR 문서를 함께 본다.

```json
GET polaris-audit-*/_search
{ "query": { "bool": { "filter": [
  { "range": { "@timestamp": { "gte": "2026-09-14T10:00:00Z", "lt": "2026-09-14T10:30:00Z" } } },
  { "range": { "http_status": { "gte": 500 } } } ] } },
  "sort": [ { "@timestamp": "asc" } ] }
```

### 7.2 감사 — "누가 언제 어떤 권한을 받았나"

1. `report_type: resource` 에서 `resource_kind: catalog-role` 이고 `writes > 0` 인 윈도우를 찾는다.
   그 `writes` 가 곧 부여된 권한 수다.
2. 해당 윈도우 시각으로 상세의 `Adding grant ...` 문서와 `PUT .../grants` 액세스 문서를 대조한다.
3. 규칙 4·5에 의해 모든 PUT/DELETE/management POST 는 전건 보존되므로, **요약의 숫자와 상세의 건수는
   일치해야 한다.** 불일치는 곧 결함 신호다.

### 7.3 이상 탐지 — 비정상 클라이언트

`report_type: principal` 에서 `auth_denied` 급증 또는 `requests` 급증을 추적한다. 개별 요청을 다 저장하지
않아도 **주체별 추이는 요약만으로 완전히 보인다**는 것이 이 설계의 요점이다.

---

## 8. 적용 계획 및 검증

| 단계 | 작업 | 완료 기준 |
|---|---|---|
| 1 | 인덱스 템플릿 적용 (`polaris-audit-*`) | 매핑 조회에서 date/long 타입 확인 |
| 2 | Lua 필터 롤 (요약 필드 형식) | 파드 재기동 후 신규 문서 생성 확인 |
| 3 | ISM 정책 등록 (30일) | 정책이 신규 인덱스에 부착됨 |
| 4 | Fluent Bit 출력 대상 전환 | `polaris-audit-*` 에 문서 유입 |
| 5 | **윈도우 30초 → 1800초 복귀** | 요약 문서 수가 예상 범위로 감소 |
| 6 | 하루 실측 | §6 추정치를 실측으로 대체 |

**적용 순서가 중요하다.** Lua 를 먼저 롤하고 그 다음 템플릿을 적용한다. 반대로 하면, 빈 문자열을 쓰는
구버전 Lua 의 문서가 `date` 필드에서 **`_bulk` 응답은 HTTP 200 인데 항목 단위로 거부**되는 무성 실패가
발생한다.

검증 게이트(각 항목은 통과/실패가 명확해야 하며, **0건 반환은 통과가 아니다**):

- `access_seen - access_counted == access_kept`
- `sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors`
- `max_record_time - min_record_time <= window_seconds`
- 임의의 30분 구간에서 요약의 `errors_5xx` 합 == 상세의 `http_status >= 500` 문서 수
- 임의의 롤 행 `writes` == 같은 구간 상세의 `PUT .../grants` 문서 수

---

## 9. 알려진 제약과 미해결 항목

적용 전에 인지하고 있어야 할 사항이며, 일부는 본 정책의 정확도에 직접 영향을 준다.

| # | 항목 | 영향 | 상태 |
|---|---|---|---|
| 1 | **애플리케이션 로그(DEBUG SQL)가 분리되지 않음** | 실제 용량의 다수. 액세스 필터만으로는 절감 한계 | **최우선 미해결** |
| 2 | **요약 윈도우 라벨이 3.673초 밀림** | 경계 직후 트래픽이 직전 윈도우 행에 집계됨. 윈도우 단위 정합성 검증이 어긋남 | 원인 규명 완료(2026-09-14), 수정 전 |
| 3 | 윈도우 30초로 운영 중 | 요약 문서가 약 60배 부풀어 있음 | 1800초 복귀 필요 (§8 단계 5) |
| 4 | 인덱스 템플릿 미적용 | 동적 매핑 사고 재발 가능 | §8 단계 1 |
| 5 | multiline 병합 | 깨지면 §3.3 grant 로그가 쪼개짐 | 수집 설정 확인 필요 |
| 6 | Polaris 오토스케일 시 로그 파일 공유 | 다중 파드가 한 로그를 append, 요약 `report_seq` 연속성 훼손 | 설계 결정 대기 |
| 7 | 4개 API 가 잘못된 요청에 500 응답 | `errors_5xx` 가 실제 장애가 아닌 경우 발생 (`getToken`, `createNamespace`, `renameTable`, `renameView`) | Polaris 측 이슈, 재현 확인됨 |

7번은 알림 설계에 직접 영향을 준다. **`errors_5xx > 0` 만으로 장애 알림을 걸면 오탐이 난다** — 해당 4개
오퍼레이션은 제외하거나, 별도 임계값을 둔다.

---

## 10. 요약

- Polaris 전용 인덱스 `polaris-audit-*` 를 신설하고 **보관 30일**로 한다. `kube-fb` 는 건드리지 않는다.
- 적재 대상은 **오류·변경·인증 실패 전건**과 **30분 단위 요약**이다. 성공한 조회는 세기만 한다.
- 총량은 언제나 보존된다 — 적재하지 않은 요청도 요약 카운터에 반영된다.
- 스펙 정상치 기준 30일 보관 용량은 **약 11 GB** 로, 전량 적재 대비 약 1/27 이다.
- 적용 전 해결이 필요한 항목은 §9 의 1·2·3·4번이다.
