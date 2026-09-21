# Polaris API–SQL 프로파일 — 2026-09-03 실행 결과

**읽는 법과 각 컬럼의 의미는 [`doc-api-sql-profile-guide-ko.md`](doc-api-sql-profile-guide-ko.md)에 있습니다.**
이 문서는 그 워크북 세 개가 실제로 무엇을 보여줬는지만 다룹니다. 스윕을 다시 돌리면 이 문서가 교체 대상입니다.

- 대상: Polaris 1.3.0-incubating, realm `POLARIS`, **순정 업스트림 스키마**
- 근거 런: `apiexplain-{admin,authorized,unauthorized}-20260903-1101xx.json`
- 워크북: `reports/api-explain-{case}-latest.xlsx` (2026-09-03 빌드)
- 영문 대응본: `reports/doc-api-index-findings-latest.md`

---

## 1. 결론

> **43개 오퍼레이션 × 3개 신원 = 129개 (케이스, API) 쌍 전부가 `grant_records`를 Seq Scan 합니다.**
> 60,815행 테이블 전체를, 요청마다, 거절되는 요청까지 포함해서 읽습니다.

`Summary` 시트의 `scans_grant_records`가 세 파일 모두에서 43/43 TRUE이고,
`fully_index_served`는 세 파일 모두에서 43개 전부 FALSE입니다.

이것으로 `doc-index-audit.md`가 2026-08-20부터 **INCONCLUSIVE**로 들고 있던
`grant_records_by_grantee` 가설이 확정됩니다.

---

## 2. 케이스별 규모

| 케이스 | API | statement 발생 | (SQL, params) 쌍 | `Cost` 행 | `Shapes` 행 | `Unplanned` 행 | grant_records 스캔 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `unauthorized` | 43 | 390 | 33 | 33 | 6 | 0 | **43 / 43** |
| `authorized` | 43 | 460 | 93 | 91 | 18 | 2 | **43 / 43** |
| `admin` | 43 | 564 | 138 | 128 | 21 | 13 | **43 / 43** |

**신원이 강해질수록 쿼리 종류가 늘어납니다** — 33 → 93 → 138. 거절당한 요청은 인가 판정에서
멈추므로 그 뒤의 도메인 쿼리를 발행하지 않습니다. 그런데도 스캔 컬럼은 세 줄 모두 43/43입니다.

리플레이 시점의 테이블 볼륨 (세 케이스 공통):

| 테이블 | 행 수 |
|---|---:|
| `entities` | 9,646 |
| `grant_records` | 60,815 |
| `policy_mapping_record` | 0 |
| `principal_authentication_data` | 1,108 |

인덱스 상태: **absent** — `idx_grant_records_grantee`는 스키마가 만들지 않으며, 이 측정을 위해 만들지도 않았습니다.

---

## 3. 두 조회, 엇갈린 운명

`grant_records`가 가진 인덱스는 기본 키 하나뿐입니다.

```sql
PRIMARY KEY (realm_id, securable_catalog_id, securable_id,
             grantee_catalog_id, grantee_id, privilege_code)
```

| 조회 | 술어 | 플랜 | 인덱스 | 추정 행 | 추정 비용 |
|---|---|---|---|---:|---:|
| SELECT — **securable** | `realm_id, securable_catalog_id, securable_id` | Index Only Scan | `grant_records_pkey` | 20 | 14.11 |
| SELECT — **grantee** | `realm_id, grantee_catalog_id, grantee_id` | **Seq Scan** | — | 1 | 1637.26 |
| DELETE | `(grantee… ) OR (securable… )` | ModifyTable, **Seq Scan** | — | 1 | 1941.34 |
| INSERT | (VALUES — 술어 없음) | ModifyTable, Result | — | 0 | 0.01 |

**securable** 조회는 키의 **선두 3개 컬럼**을 제약하므로 그대로 서빙됩니다.
**grantee** 조회는 1, 4, 5번 컬럼을 제약합니다 — 접두사가 `realm_id` 뒤에서 끊기므로
PostgreSQL이 키를 선택적으로 쓸 수 없고, 테이블을 읽습니다.

> **플래너는 한 행이 나올 것을 예상하면서 60,815행을 읽습니다** (`plan_rows = 1`, `rows_scanned = 60,815`).

이 간격이 이 분석 전체의 요점입니다. 다만 **비율로 환산하지 마십시오** — 워크북 `Provenance`가
말하는 대로, 두 숫자는 비례하지 않습니다. 60,815행을 순차로 읽는 것은 단일 행 인덱스 탐색의
약 194배 비용이지 60,815배가 아닙니다. 순차 읽기는 같은 수의 랜덤 인덱스 하강보다
**행당 훨씬 쌉니다**. 그리고 둘 다 지연시간이 아닙니다.

### 비용이 어디에 몰려 있나 (`Cost` 시트)

케이스 총 `cost_units` 중 `grant_records` Seq Scan이 차지하는 몫:

| 케이스 | grant_records Seq Scan 비중 | 그중 단일 최대 행 |
|---|---:|---:|
| `unauthorized` | **95.5 %** | 0.9368 (51회, 43개 API) |
| `authorized` | **94.1 %** | 0.7735 (45회, 43개 API) |
| `admin` | **93.9 %** | 0.6202 (45회, 43개 API) |

케이스 **내부** 순위이며 케이스 간 비교는 불가합니다. 그럼에도 세 케이스 모두에서
한 종류의 쿼리가 계획 비용의 90% 이상을 차지한다는 사실 자체는 신원과 무관합니다.

---

## 4. 거절도 값을 치릅니다

문제의 조회는 `loadAllGrantRecordsOnGrantee`이고, 인증된 모든 요청의 인가 경로 위에 있습니다.
**인가 판정보다 먼저** 발화하므로, 403으로 끝나는 요청도 스캔 비용을 전부 치릅니다.

| 케이스 | 2xx | 403 | 404 | grantee 조회 발생 | 스캔에 도달한 API |
|---|---:|---:|---:|---:|---:|
| `unauthorized` | 2 | 22 | 19 | 51 | 43 / 43 |
| `authorized` | 29 | 5 | 9 | 45 | 43 / 43 |
| `admin` | 41 | 1 | 1 | 45 | 43 / 43 |

`unauthorized`는 43개 중 **2개만 성공**했습니다. 그 신원의 성공률과 무관하게, 43개 전부가
60,815행 스캔을 유발했습니다. 2026-08-24의 결과(거절 6,000건, 각각 grantee 조회 1.00회)를
독립적으로 재현하며, 이번에는 그 횟수 뒤의 **플랜**까지 붙어 있습니다.

---

## 5. 대조군 — `entities`는 잘 서빙됩니다

문제는 `grant_records`에 국한되고, 그중에서도 한 방향에만 있습니다.

- 세 케이스의 `Distinct` 시트를 통틀어 **`entities`를 순차 스캔하는 행은 0개**입니다.
- 스윕 전체에서 실제 사용이 관측된 인덱스: `constraint_name`, `entities_pkey`, `grant_records_pkey`, `idx_entities`, `policy_mapping_record_pkey`
- 업스트림은 `entities`에 키와 유니크 제약 위에 `idx_entities`와 `idx_locations`를 얹고, `policy_mapping_record`에는 `idx_policy_mapping_record`를 줍니다.

> **`grant_records`는 매 요청마다 읽히는 유일한 테이블이면서, 키 말고는 아무것도 없는 유일한 테이블입니다.**

`Schema` 시트가 이걸 한 줄로 보여줍니다 — 대상 테이블의 인덱스 인벤토리에 `grant_records_pkey` 하나,
`in_upstream_schema = TRUE`.

---

## 6. 이건 업스트림 문제이지 이 배포의 문제가 아닙니다

스키마 권위는 `schema_v3.sql`이고 ASF 라이선스 헤더와 *"Changes from v2: Added `events` table"* 을 달고 있는
Apache Polaris 파일입니다. 옆의 로컬 `schema.sql`은 구조적으로 동일합니다 — 주석, `IF NOT EXISTS`,
`ON CONFLICT`, `COMMENT ON`을 정규화하면 12개 문장이 모두 일치하고, 멱등성과 문서화에서만 다릅니다.

업스트림이 스스로 말하고 있습니다 (`schema_v3.sql:57`):

```sql
-- TODO: create indexes based on all query pattern.
CREATE INDEX IF NOT EXISTS idx_entities ON entities (realm_id, catalog_id, id);
```

이 TODO는 `entities` 인덱스 두 개 바로 위에 있습니다. **`grant_records`는 차례가 오지 않았습니다.**

---

## 7. 이번 실행에만 걸리는 한계

방법 자체의 한계는 가이드 §5에 있습니다. 여기 있는 것은 이 런에 고유한 것들입니다.

- **볼륨 하나 기준입니다.** 모든 플랜은 `grant_records` 60,815행 상태에 상대적입니다. 병렬화 전환점은 약 160K, 테이블이 `shared_buffers`를 벗어나는 지점은 320K–640K 사이로 측정되었습니다. **더 큰 렘은 "더 많은 이것"이 아니라 다른 체제입니다.**
- **`policy_mapping_record`는 0행**이라 문장은 기록되었지만 플랜으로 측정 불가입니다. 빈 테이블에 대한 플랜은 전부 비슷하게 생겼습니다.
- **재생되지 못한 문장이 있습니다** (`Unplanned` 시트):
  - **영구 (admin 3건)** — `principal_authentication_data`는 비밀 자료를 담고 있어 캡처 시점에 파라미터가 리댁션됩니다. 영원히 재생되지 않습니다.
  - **복구 가능 (admin 7건, authorized 2건)** — 로그 파싱 결함으로 텍스트가 손상된 `grant_records` 문장 6건과 비동기 `events` INSERT. 6건 모두 캐스케이드 삭제 읽기 경로 위에 있습니다. 파서는 수정되었고 다음 드라이브에서 돌아옵니다.
  - `Unplanned` 행 수(admin 13)에는 *"스윕의 작업 목록에 없음"* 으로 표시된 `redacted` 3건이 더 있습니다. `Summary`의 `skipped` 합계(admin 10, authorized 5)는 **API별로 중복 계상**되므로 `Unplanned` 행 수와 같지 않습니다 — 단위가 다릅니다.
- **제안된 인덱스가 이 문제를 고치는지는 여기서 검증되지 않았습니다.** 이 스윕은 출하된 스키마를 재고 의도적으로 아무것도 만들지 않습니다.

---

## 8. 다음

1. **인덱스 가설 검증은 별도 작업입니다.** `02b_grant_scale_sweep.ipynb`와 `reports/doc-grant-scale-sweep-latest.md`가 그 자리입니다. 인덱스를 만든 상태의 측정은 이 스윕에 절대 섞지 않습니다.
2. **제안은 코드에 남기되 적용하지 않습니다** — `schema_audit.INDEX_HYPOTHESES`가 그 자리이고, 권고이지 적용된 변경이 아닙니다.
3. **복구 가능한 9건은 다음 드라이브에서 회수됩니다.** 전부 캐스케이드 삭제 경로라, 회수되면 DELETE 쪽 그림이 지금보다 정확해집니다.
4. **업스트림 제보**는 가설이 확정된 뒤의 단계입니다 — 로컬에서 인덱스를 만들고 전후 델타를 기록한 다음, Polaris `main`을 확인하고 제보합니다.

---

## 부록 — 이 문서의 숫자를 검증하는 법

```bash
cd diagnostics/api-sql-profile
python3 _check_guide_figures.py
```

`reports/api-explain-{case}-latest.xlsx`와 그 워크북이 지목한 런 JSON에서 수치를 다시 계산해
이 문서와 가이드 문서의 주장과 대조합니다. 하나라도 어긋나면 non-zero로 종료합니다.
**손으로 타이핑한 숫자를 담은 리포트는 그것을 만든 런에서 표류하고, 아무도 재현을 시도하기 전까지 알아채지 못합니다.**
