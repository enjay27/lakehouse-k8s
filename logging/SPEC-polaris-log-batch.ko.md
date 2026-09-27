# Polaris 로그 배치 — 동작 명세와 스크립트 로직

> **상태 (2026-09-28)**
> - Polaris 파드별 로그 파일 + PVC `polaris-logs-pvc`: **로컬(OrbStack)에 적용·검증 완료**.
> - 배치: **Polaris 와 별개로 빌드·배포**한다 — 자체 이미지 + 자체 차트 + 자체 릴리스. 스크립트와 테스트는 완료,
>   **이미지 빌드·차트 렌더·첫 실행은 아직** (§17, `logging/HANDOFF-polaris-log-batch-2026-09-28.md`).
>
> | 무엇 | 어디 |
> |---|---|
> | 배치 스크립트 | `images/polaris-log-batch/polaris_log_batch.py` (Python 3.10+, 표준 라이브러리만) |
> | 이미지 | `images/polaris-log-batch/Dockerfile` (`python:3.11-slim`, uid/gid 10000/10001) |
> | 배포 차트 | `charts/polaris-log-batch/` → 릴리스 `polaris-log-batch` (ServiceAccount · Role · RoleBinding · CronJob) |
> | 로그 PVC | `logging/k8s/polaris-logs-pvc.yaml` (Polaris 보다 먼저, 릴리스 밖에서 생성) |
> | Polaris 로그 설정 | `charts/polaris/values.yaml` — `logging.file`, `extraEnv` |
> | 테스트 | `tests/test_polaris_log_batch.py` (프레임워크 26), `tests/test_polaris_log_policy.py` (정책 14) |
> | Lua 동등성 검사 | `logging/scripts/step16-batch-lua-parity.py` |
> | 공유 파일 손실 측정 | `logging/scripts/step15-shared-file-size-rotation-test.sh`, `.memory/active-issues/platform.md` `#48` |
> | 결정 이력 | `logging/PLAN-polaris-log-batch-2026-09-27.md` |
>
> 1부는 "무엇을 왜", 2부는 스크립트가 **실제로 어떻게** 하는지, 3부는 배포·운영이다.

---

# 1부 — 설계

## 1. 전체 흐름과 책임 경계

```
Polaris 파드 ──JSON 로그, 매시 .gz 회전──▶ PVC  polaris-logs-pvc  (/deployments/logs)
                                                  ▲ 읽기·쓰기            ▲ 공유하는 것은 이 PVC 하나
CronJob polaris-log-batch (매시 03분, KST) ──────┘ processed-logs/ · aggregated-logs/ · malformed/
──────────────────────────── 여기까지 우리 팀 ────────────────────────────
관측팀 ──PVC 에서 수집──▶ OpenSearch
```

- 실시간 모니터링은 요구사항이 아니다. 1시간 단위 배치로 충분하다.
- Fluent Bit 은 우리 팀 소관이 아니므로 이 경로에서 쓰지 않는다. 기존 Fluent Bit Lua 필터
  (`releases/fluent-bit/polaris_access_log.lua`, 정책 v5) 의 **판정·집계 규칙을 배치로 옮겼다** (§8, §9).
- 배치는 Polaris 차트와 **독립적으로 빌드·배포**한다. 두 릴리스가 공유하는 쿠버네티스 객체는 PVC 하나뿐이다.

## 2. Polaris 쪽: 로그 파일

| 항목 | 설정 (`charts/polaris/values.yaml`) | 이유 |
|---|---|---|
| 파일 | **파드마다 한 파일** `polaris-${HOSTNAME}.log` (`HOSTNAME` = 파드 이름) | 한 파일을 여러 파드가 쓰면 회전이 서로를 덮어쓴다 (§2.1) |
| 형식 | JSON (`QUARKUS_LOG_FILE_JSON_ENABLED=true`), **한 줄 = 한 이벤트** | 줄 단위로 읽고 판정하기 위해 (스택트레이스도 한 줄) |
| 회전 | `fileSuffix: .yyyy-MM-dd-HH.gz` — 매시, 압축 | 배치가 시간 단위다 |
| 시간대 | `TZ=Asia/Seoul` | 회전 파일 이름이 JVM 시간대를 따른다 |
| 크기 회전 | `maxFileSize: 2Gi`, `maxBackupIndex: 50` | 시간 접미사를 쓰면 크기 회전을 끌 수 없다. 한 시간에 도달할 수 없는 크기로 둔다. 50 을 넘는 `.N` 은 Quarkus 가 지운다 |
| 재시작 시 회전 | 끔 (`QUARKUS_LOG_FILE_ROTATION_ROTATE_ON_BOOT=false`) | 컨테이너 재시작이 같은 시간 이름으로 두 번 회전하지 않게 |
| 저장소 | `logging.file.storage.existingClaim: polaris-logs-pvc` | `helm uninstall` 이 로그를 지우지 않고, 배치 릴리스가 따로 마운트한다 |

> Polaris 차트는 **ConfigMap 만 바뀌는 업그레이드에서 파드를 재시작하지 않는다** (config checksum 주석이 없다).
> 로그 설정을 바꾸면 `kubectl rollout restart deploy/benchmarks-polaris` 가 필요하다.

### 2.1 왜 파드별 파일인가 — 측정 결과

같은 파일을 두 파드가 쓰면, 각 JVM 이 **자기 시계로 따로** 파일 이름을 바꾸고 새로 연다. 한쪽이 회전하는
순간 다른 쪽은 이미 이름이 바뀐(압축 후 삭제될) 파일에 계속 쓴다.

| 방식 | 부하 4000건 | 실제 API 트래픽 327건 |
|---|---|---|
| 공유 파일 (1차) | 1780건 유실 (44.5%) | — |
| 공유 파일 (2차) | 1769건 유실 (44.2%) | **200건 유실 (61%)** |
| **파드별 파일** | **0건 유실** | **0건 유실** |

(2 파드, 50 kB 마다 회전으로 강제한 시험. 운영 설정에서도 HPA 확장·롤링 업데이트 때 같은 일이 일어난다 —
2026-09-27 실제로 시간 18의 로그가 이렇게 지워졌다.)

### 2.2 회전은 "게으르다"

Polaris(JBoss 로그 핸들러)는 시계로 회전하지 않는다. **정각 이후 첫 로그 줄을 쓰기 직전에** 회전한다.
- 조용한 시간에는 회전 파일이 **아예 생기지 않는다**.
- 유휴 파드의 현재 파일은 몇 시간 동안 이전 시간의 줄을 담은 채 남아 있을 수 있다.
- 한 파일에는 **한 시간의 줄만** 들어간다 (새 시간의 첫 줄이 회전을 일으키므로). 예외는 경계에서 스레드 경합으로
  몇 ms 이른 줄이 다음 파일 앞부분에 섞이는 경우뿐이다.
- 그래서 배치는 회전 파일만 믿지 않고 **현재 파일도 함께 읽는다** (§4).

## 3. PVC 디렉터리 구조

```
/deployments/logs/
  polaris-<pod>.log                       현재 파일 (Polaris 가 쓴다; 배치는 읽기만, 고아만 옮긴다)
  polaris-<pod>.log.2026-09-28-10.gz      매시 회전 파일 (크기 회전 시 …-10.1.gz, …-10.2.gz)
  processed-logs/20260928-10.jsonl        시간 10 의 적재 대상 이벤트
  aggregated-logs/20260928-10.jsonl       시간 10 의 요약 1행 + 리소스/principal/버린 logger 행
  malformed/20260928-10.jsonl             시간 10 에 읽지 못한 줄
  malformed/files/                        압축이 깨진 회전 파일
  done/20260928/                          처리가 끝난 회전 파일, 고아 파일(*.orphan)
  .state/checkpoint.json                  진행 기록
  .state/lock                             동시 실행 방지 (flock)
  .tmp/                                   원자적 쓰기용 임시 파일 (같은 파일시스템이어야 rename 이 원자적)
  legacy-shared/ sizetest/ movetest/      과거 시험의 잔여물 — 배치는 하위 디렉터리를 읽지 않는다
```

파일 이름의 시간은 모두 **KST**, `YYYYMMDD-HH` 는 그 시간의 시작 (`10` = 10:00:00 ~ 10:59:59.999…).

## 4. 줄 선택 규칙 — 파일이 아니라 타임스탬프로 고른다

매시 03분 실행이 시간 H(예: 10시)를 처리할 때:

1. **모든 파드의 회전 파일과 현재 파일**을 후보로 한다 (최상위 디렉터리, 이름이 `polaris-benchmarks-polaris-…` 인 것).
2. 그중 **마지막 수정 시각이 H 시작 − 30초 이후**인 파일만 연다. 그 전에 마지막으로 쓰인 파일에는 H 의 줄(또는
   §8.1 의 요청 ID 매칭에 필요한 앞 30초의 줄)이 있을 수 없다.
3. 각 줄의 `timestamp` 가 **[10:00:00.000000000, 11:00:00.000000000)** 에 들면 시간 10 의 줄이다.
   11:00~11:03 의 줄은 파일에 그대로 두고 다음 실행이 가져간다.
4. 출력은 **정렬을 목적으로 하지 않는다** (OpenSearch 가 `timestamp` 로 정렬한다). 다만 정책 판정을 위해 내부에서
   타임스탬프 순으로 평가하므로 결과적으로 시간순으로 나온다.

따로 처리할 경우가 사라진다.
- **늦게 도착하는 파일이 없다.** 현재 파일까지 읽으므로 11:03 에는 10시의 줄이 전부 디스크에 있다.
- **경계 스큐도 자연히 처리된다.** 10:59:59.9 의 줄이 11시 파일 앞부분에 들어가도 타임스탬프로 10시에 들어간다.
- **고아 파일도 그냥 또 하나의 파일이다** (§6).

### 4.1 Polaris 가 쓰고 있는 파일 읽기
- **줄바꿈으로 끝난 줄만** 센다. 쓰는 도중의 마지막 줄은 무시한다.
- 그 마지막 줄이 끝내 완성되지 않으면(파드가 쓰다가 죽음) 고아 처리 때 `malformed/` 로 간다 (§6).

### 4.2 읽지 못한 줄 (malformed)
JSON 객체가 아니거나 `timestamp` 가 없거나 해석할 수 없는 줄은 자기 시간을 모른다. **같은 파일에서 바로 앞의 정상
줄의 시간**에 기록한다 (앞이 없으면 뒤, 그것도 없으면 회전 파일 이름의 시간, 그것도 없으면 파일 수정 시각의 시간).
그래서 한 번만, 한 시간의 `malformed/` 파일에만 나온다.

### 4.3 대상 시간과 실행
- 실행 주기: 매시 03분 (CronJob). 시간 H 는 **H+1:01 이후**부터 처리 대상이다 (60초 여유).
- 체크포인트의 다음 시간부터 **완료된 가장 최근 시간까지** 차례로 처리한다 — 놓친 실행은 자동으로 따라잡는다
  (한 번에 최대 72시간, 나머지는 다음 실행).
- 첫 실행(체크포인트 없음)은 디스크에 있는 **가장 이른 정상 줄의 시간**부터 시작한다 (한 번 전부 읽는다).
- 줄이 하나도 없는 시간도 **빈 processed 파일과 0 으로 채운 요약**을 발행한다. "처리 완료·0건" 과 "아직 처리 안 됨"
  을 구분하기 위해서다.
- 동시 실행 방지: `.state/lock` 파일 락 + CronJob `concurrencyPolicy: Forbid`.

## 5. 정확히 한 번 — 체크포인트와 원자적 쓰기

- 진행 기록은 **시간 단위**다 (`last_published`). 한 번 발행한 시간은 다시 열지 않는다.
- 한 시간의 발행 순서:
  1. `malformed/`(있을 때), `processed-logs/`, `aggregated-logs/` 를 차례로 — 각각 `.tmp/` 에 쓰고 fsync →
     `os.replace` 로 제자리에 → 디렉터리 fsync
  2. **그다음에** 체크포인트에 그 시간을 기록 (체크포인트 자체도 같은 방식으로 원자적 쓰기)
  3. 정리 (§7)
- 어디서 죽든 다음 실행은 기록되지 않은 시간을 **처음부터 다시** 만든다. 원본 파일은 제자리에 있으므로 같은 줄,
  같은 `event_id` 가 나온다.
- `event_id` = 원본 줄 바이트의 SHA-1. 같은 줄을 현재 파일에서 읽든 나중에 회전된 `.gz` 에서 읽든 같은 값이다.
  관측팀은 이것을 OpenSearch `_id` 로 쓰면 재적재해도 중복이 생기지 않는다.
- **관측팀의 완료 신호**: `aggregated-logs/H.jsonl` 은 `processed-logs/H.jsonl` **다음에** 쓰인다. aggregated 파일이
  보이면 그 시간의 processed 파일은 완성본이다.

## 6. 고아 파일 — 파드가 사라진 뒤 남은 현재 파일

HPA 축소·롤아웃·축출로 파드가 없어지면 그 파드의 `polaris-<pod>.log` 는 **영원히 회전되지 않는다**
(2026-09-27 `2tklb` 파드에서 실제 발생).

**고아 = 두 조건을 모두 만족하는 현재 파일**
1. **파드가 없다** — 실행 시작 시 Kubernetes API 로 Polaris 파드 목록을 조회하고(selector
   `app.kubernetes.io/instance=benchmarks-polaris,app.kubernetes.io/name=benchmarks-polaris`, 종료 중인 파드 포함),
   파일 이름의 파드가 목록에 없다.
2. **파일이 완결됐다** — 마지막 완결 줄의 시간이 지금 발행하는 시간 이하이고, 120초 넘게 수정이 없다.

**왜 둘 다인가**
- (1) 만으로는: API 조회와 디렉터리 스캔 사이에 새로 뜬 파드의 파일을 고아로 오인할 수 있다.
- (2) 만으로는: "사라진 파드" 와 "살아 있지만 조용한 파드" 를 구분할 수 없다.
- 둘 다 요구하므로 **살아 있는 파드의 파일은 절대 옮기지 않는다** (JVM 이 열어 둔 파일을 건드리지 않는다).

**처리**
- 고아 파일의 줄은 §4 에 따라 **다른 파일과 똑같이** 자기 시간에 처리된다. 특별 경로가 없다.
- 그 시간이 발행된 뒤 `done/YYYYMMDD/polaris-<pod>.log.<YYYY-MM-DD-HH>.orphan` 으로 옮긴다
  (담긴 시간을 이름에 붙여, 같은 이름의 파일이 나중에 생겨도 충돌하지 않게).
- 마지막 줄이 잘려 있으면 그 조각은 발행하는 시간의 `malformed/` 로 간다.
- **API 조회에 실패하면 그 실행에서는 어떤 현재 파일도 옮기지 않는다.** 처리 자체는 계속한다.
- 살아 있지만 조용한 파드의 파일(마지막 줄이 발행하는 시간보다 이전)은 옮기지 않고 요약의 `idle_log_files` 에 보고만.

## 7. 정리와 보존

| 대상 | 규칙 |
|---|---|
| 회전 파일 `…-HH[.N].gz` | 시간 HH 이하가 발행되면 `done/<HH 의 날짜>/` 로. (HH 파일에는 HH+1 의 줄이 들어갈 수 없다) |
| 현재 파일 | 고아가 아니면 옮기지 않는다 |
| 압축이 깨진 `.gz` | 수정 후 120초 미만이면 압축 중일 수 있으니 **그 시간 처리를 미룬다**(다음 실행에 재시도). 그 이상이면 `malformed/files/` 로 격리하고 요약 `corrupt_files` 에 기록 |
| 같은 이름이 이미 있으면 | 덮어쓰지 않고 `.1`, `.2` … 를 붙인다 |
| 보존 | `processed-logs/`, `aggregated-logs/`, `malformed/`, `done/` 의 파일을 **수정 시각 기준 3일** 지나면 삭제. 출력 파일의 수정 시각 = 발행 시각. `done/` 으로 옮긴 파일은 이름만 바뀌므로 **원래 파일의 마지막 기록 시각**을 따른다 |
| 체크포인트 | 발행 시각이 3일 지난 시간 항목은 `hours` 에서 지운다 (`last_published` 는 유지) |

관측팀은 **3일 안에** 수집해야 한다.

## 8. 적재 정책 — processed-logs 에 무엇이 남는가

기존 Lua 필터(정책 v5)와 **같은 규칙**이다. 위에서부터 먼저 맞는 규칙이 이긴다.

| # | 조건 | 결과 |
|---|---|---|
| * | 모든 줄: 마스킹 안 된 `clientSecret` | `<redacted>` 로 치환, `secret_redacted: true` (판정 전에) |
| 1 | level `ERROR` / `WARN` | **적재** (액세스 줄이면 파싱 필드는 붙지만 집계는 안 된다 — Lua 와 동일) |
| 2a | `IcebergCatalog` 의 `Successfully committed to table/view … in N ms` | 커밋 시간을 해당 테이블/뷰 행에 집계 (그 뒤 2c) |
| 2b | 허용 목록 logger (`IcebergExceptionMapper`, `PolarisServiceImpl`) | 같은 요청의 액세스 줄 상태로 결정 (§8.1) |
| 2c | 그 밖의 애플리케이션 로그 | 버림 — logger 별로 셈 (`app_dropped`) |
| 3′ | 액세스 줄, 상태 404 | 집계만 (`counted_404`) |
| 3 | 액세스 줄, 상태 ≥ 400 또는 파싱 실패 | **적재** — 전건 |
| 4 | PUT / DELETE / PATCH | **적재** — 전건 |
| 5 | POST: `/api/management/` 하위 | **적재** — 전건 (생성·권한 변경) |
|   | POST: 그 밖 (카탈로그 데이터 평면) | 집계만 (`counted_post`) |
| 6 | GET / HEAD 성공 | 집계만 (`counted_read`) |
| 7 | 그 외 | 적재 |

보장: 인가 실패(401·403) 100% 보존, 신원·권한 변경 100% 보존, **버린 것은 반드시 숫자로 남는다**.

### 8.1 요청 ID 매칭 (허용 목록 로그)
예외 사유·권한 변경 로그는 보통 액세스 줄보다 **몇 ms 먼저** 찍힌다. 같은 `mdc.requestId` 의 액세스 줄 상태로:
- **404** → 그 앱 로그도 버린다 (`app_dropped_404`)
- 그 외 상태 → 적재
- 앞뒤 **30초 안에 액세스 줄이 없으면** → 적재하고 `held_orphan: true` 표시 (`held_orphans`)
- 요청 ID 가 없으면 → 즉시 적재

Lua 는 레코드를 메모리에 잡아 두고 액세스 줄을 기다렸다. 배치는 한 시간 전체와 **앞뒤 30초**를 이미 가지고 있으므로
양쪽을 바로 본다. 10:59:59.995 의 사유 로그와 11:00:00.005 의 404 처럼 **시간 경계를 넘는 짝도** 맞춘다.

### 8.2 적재 문서의 모양
- Polaris 원본 JSON 그대로 + 액세스 줄이면 파싱 필드: `client_ip`, `user_principal_name`, `http_method`, `api_path`,
  `http_status`(정수), `response_size`(정수, `-` 는 0) — 실패 시 `access_log_parse_error: true`.
- tier 2 와 같은 필드 정리: `processName`, `loggerClassName`, `processId`, `ndc` 제거.
- 추가: `event_id` (원본 줄 SHA-1), `log_hour` (`YYYYMMDD-HH`), 경우에 따라 `secret_redacted`, `held_orphan`.
- 시간 필드는 **Polaris 원래 이름 `timestamp` 그대로** (Fluent Bit 은 `_time` 으로 바꿨었다).

## 9. 집계 — aggregated-logs 의 행 (리포트 스키마 7)

한 시간 파일 = **요약 1행(맨 앞)** + 리소스 행 + principal 행 + 버린 logger 행. 필드 의미는 리포트 스키마 v6
(`logging/SCHEMA-report.md`) 와 같고 배치에 맞춘 차이만 있다.

| 행 (`report_type`) | 내용 |
|---|---|
| `summary` | 시간당 1건. 액세스 줄 수·적재·집계, 오류 수, 404, 버린 앱 로그, 보류 고아, 상한 넘침 + 배치 정보 (§9.2) |
| `resource` | 리소스별 `requests reads writes errors errors_4xx errors_5xx auth_denied response_bytes`, 2xx 표본이 있으면 `last_read_bytes`/`last_write_bytes`, 커밋이 있으면 `commit_count commit_ms_sum commit_ms_min commit_ms_max` |
| `principal` | 호출 주체별 같은 카운터 (`last_*_bytes` 없음) |
| `app_dropped` | 버린 logger 별 `dropped` (새 logger 등장 감지용) |

모든 행에 공통: `schema_version: 7`, `report_type`, `window_start`, `window_end`, `window_seconds: 3600`,
`_time`(= `window_end`).

**리소스 키**는 URL 이 아니라 리소스다: 쿼리스트링을 떼고 21개 패턴을 순서대로 맞춰 **맞은 구간까지** 자른다.
`/tables/t/metrics` 와 `/tables/t` 는 같은 행, 권한 부여 `/catalog-roles/cr/grants` 는 롤 `cr` 행, 할당
`/principal-roles/pr/catalog-roles/c` 는 principal role `pr` 행. 맞는 패턴이 없으면 경로 전체가 키(`other`).
커밋 로그의 `cat.a.b.t` 는 `/api/catalog/v1/cat/namespaces/a%1Fb/tables/t` 로 바꿔 같은 행에 붙인다.

**행 수 상한**: 리소스 500, principal 200, 버린 logger 50 → 넘치면 `__other__` 한 행. 합계는 정확하고 키별 상세만
잘린다. 오류 요청은 원칙적으로 **새 행을 만들지 못하고** `__errors__` 로 간다 (없는 이름을 두드리는 클라이언트가 키
공간을 채우지 못하게). 예외: 그 리소스가 그 시간에 성공·커밋한 적이 있으면 그 행, 롤(catalog-role, principal-role)
오류는 최대 100개까지 새 행을 만든다(`role_keys_forced`) — 거부된 grant 가 곧 롤 행이 답할 보안 질문이므로.

### 9.1 v6 와 다른 점

| 항목 | v6 (Fluent Bit, 스트리밍) | 7 (배치) |
|---|---|---|
| 창 | 30분/1시간 틱, 파드별 | **KST 정각 1시간, 전체 파드 합산**, 항상 완결 |
| 식별 | `hostname`, `report_seq` | 대신 `pods` (그 시간에 줄이 있던 파드 목록) |
| 없어진 필드 | `windows_skipped`, `partial_window`, `held_pending` | 창이 늘 완결이라 의미가 없다 |
| 오류 요청의 행 | **그 순간** 행이 있었으면 그 행, 아니면 `__errors__` | 그 리소스가 **그 시간 어디서든** 성공·커밋했으면 그 행 (순서 무관) |
| 평가 순서 | 도착 순서 | 타임스탬프 순서 — 상한·롤 강제 결과가 항상 같다 |
| 요청 ID 짝 | 메모리 보류, 30초 | 앞뒤 30초 조회, 시간 경계 포함 |

### 9.2 요약 행의 배치 정보와 불변식
배치 필드: `hour`, `batch_schema` (`polaris-log-batch/1`), `policy` (`policy-v5/report-v7`), `lines_in`, `processed`,
`dropped`, `malformed`, `by_pod`, `sources`(파일별 그 시간 줄 수), `corrupt_files`, `orphans_moved`, `idle_log_files`,
`pod_list_error`, `published_at`. 액세스 줄이 있던 시간에만 `min_record_time` / `max_record_time`.

**불변식** — 어긋나면 그 시간을 발행하지 않고 실패한다 (§14):
- `lines_in = processed + dropped + malformed`
- `dropped = access_counted + app_dropped_total + app_dropped_404`
- `access_kept = access_seen − access_counted`

---

# 2부 — 스크립트 로직 (`polaris_log_batch.py`)

한 파일, 표준 라이브러리만(`gzip json re fcntl hashlib ssl urllib …`). 위에서 아래로 7개 구역이다.

| 구역 | 주요 함수·클래스 | 하는 일 |
|---|---|---|
| time | `parse_ts` `floor_hour` `hour_key` `hour_from_key` `roll_hour` | 타임스탬프 해석, KST 시간 단위 계산 |
| files | `LogFile` `scan` `read_file` `last_complete_line` `parse_line` `classify` `Deferred` `Corrupt` | 파일 찾기·읽기, 줄을 시간에 배정 |
| policy | `parse_access` `redact_secret` `classify_path` `commit_key` `request_id` `bump` `HourReport` `access_status_index` `matching_status` `AuditPolicy` `PassthroughPolicy` | 정책 v5 판정과 스키마 7 집계 |
| disk | `ensure_dirs` `atomic_write` `fsync_dir` `move_unique` `load_checkpoint` `save_checkpoint` | 원자적 쓰기, 이동, 체크포인트 |
| pods | `k8s_pod_lister` | API 로 Polaris 파드 이름 목록 |
| one hour | `process_hour` `publish` `housekeep_after` `retention` | 한 시간 계산 → 발행 → 정리 |
| run | `Config` `first_hour` `run` `_run_locked` `main` | 락, 시간 루프, CLI |

## 10. 실행 흐름

```
main()                                   CLI 인자 → Config, pod_lister = k8s_pod_lister(selector) (--no-pod-list 면 없음)
└ run(cfg, now)                          now = 지금(KST) 또는 --now
  ├ ensure_dirs                          processed-logs aggregated-logs malformed done .tmp .state 생성
  ├ flock(.state/lock, 비차단)           잡혀 있으면 {"event":"skipped"} 출력 후 종료(0)
  └ _run_locked
    ├ cp    = load_checkpoint            없으면 {last_published: null, hours: {}}
    ├ files = scan(log_dir, pod_prefix)  최상위의 polaris-<prefix…>.log / .log.<시간>[.N].gz
    ├ last_ready = floor_hour(now − 60 s) − 1h
    ├ h = last_published + 1h            체크포인트가 없으면 first_hour(files) (전체 읽기)
    │     h 가 없으면(파일도 체크포인트도 없음) {"event":"idle"} 후 종료
    ├ pods = pod_lister()                실패하면 pods=None, pod_error="<예외>" — 이번 실행은 고아 이동 없음
    ├ while h ≤ last_ready and 처리 수 < 72:
    │    result = process_hour(...)      Deferred 면 {"event":"deferred"} 출력, 루프 중단(다음 실행에 재시도)
    │    --dry-run: 요약만 출력하고 다음 시간
    │    publish(result)                 malformed → processed → aggregated (각각 원자적)
    │    cp.last_published = H; cp.hours[H] = {published_at, processed, malformed, sources}; save_checkpoint
    │    housekeep_after(result)         회전 파일·고아·깨진 .gz 이동
    │    files = scan(...)               이동 후 목록 갱신
    │    {"event":"published", …요약, "moved": n} 출력
    └ (dry-run 아니면) 체크포인트의 3일 지난 hours 정리 → retention() → {"event":"retention"} (지운 게 있으면)
```

## 11. 파일과 줄 다루기

**`scan(log_dir, pod_prefix)`** — 최상위만 본다. 이름이 `ROLL_RE`(`polaris-<pod>.log.<YYYY-MM-DD-HH>[.N].gz`)면
`roll`(이름에서 시간), `CURRENT_RE`(`polaris-<pod>.log`)면 `current`. `<pod>` 가 `pod_prefix`
(`benchmarks-polaris-`)로 시작하지 않으면 제외 — 그래서 `polaris-sizetest-*` 같은 시험 파일은 읽히지 않는다.
listdir 와 stat 사이에 회전으로 사라진 파일은 조용히 건너뛴다. 결과는 이름순(결정적).

**`read_file(f, now, quiet)`**
- `roll`: `gzip` 으로 전부 풀어 줄로 나눈다. 끝의 CRC 까지 확인되므로 잘린 파일은 예외가 난다 →
  수정 후 120초 미만이면 `Deferred`(압축 중일 수 있음), 이상이면 `Corrupt`.
- `current`: 바이트로 읽어 `\n` 으로 나누고, 마지막 조각(줄바꿈 없는 꼬리)은 줄 목록에서 뺀다.

**`parse_line(raw)`** — JSON 객체이고 `timestamp` 를 `parse_ts` 로 해석할 수 있으면 `(rec, ts)`, 아니면 `(None, None)`.

**`parse_ts`** — `YYYY-MM-DDTHH:MM:SS[.소수][Z|±HH:MM]` 를 정규식으로 해석. 소수는 **마이크로초까지 자르고**(시간 판정에는
충분, 원본 줄의 나노초는 그대로 출력), 오프셋이 없으면 KST 로 본다. 결과는 KST aware datetime.

**`classify(f, lines)`** — 파일의 줄마다 `(line_no, raw, rec, ts, hour)` 를 낸다. 정상 줄의 `hour` = `floor_hour(ts)`.
읽지 못한 줄의 `hour` = 같은 파일의 직전 정상 줄 → 직후 정상 줄 → 회전 파일 이름의 시간 → 파일 수정 시각의 시간 (§4.2).
직후 줄을 알기 위해 뒤에서부터 한 번 훑어 두고, 앞에서부터 다시 돈다.

**`last_complete_line(path)`** — 파일 끝의 256 KB 만 읽어 마지막 **완결** 줄과 꼬리(줄바꿈 없는 조각)를 돌려준다.
파일이 256 KB 보다 크면 첫 조각은 잘린 줄일 수 있어 버리고, 창 안에 완결 줄이 하나도 없으면 추측하지 않고 `None`.
고아·유휴 판정에만 쓴다 (큰 현재 파일을 매시간 통째로 읽지 않기 위해).

## 12. 한 시간 계산 — `process_hour(cfg, files, h, now, pods, pod_error)`

디스크에 아무것도 쓰지 않고 결과만 만든다.

1. **창 계산**: `h0 = H 시작`, `h1 = H+1 시작`, 문맥 창 `[h0−30s, h1+30s)`.
2. **파일 읽기**: 수정 시각 < `h0−30s` 인 파일은 건너뛴다. 나머지를 `read_file` → `classify`.
   - 타임스탬프가 문맥 창 안이면 `context` 에 `{rec, ts}` 추가 (요청 ID 매칭용).
   - `hour == H` 인 줄: 정상이면 `entries` 에 `{rec, ts, raw, pod, file, line_no}`, 아니면 `malformed` 에
     `{reason, file, line_no, raw}`.
   - 파일별 H 의 줄 수를 `sources` 에. `Corrupt` 인 파일은 `corrupt` 에 기록하고 건너뛴다. `Deferred` 는 위로 던진다.
3. **고아·유휴 판정**: 모든 `current` 파일(수정 시각과 무관)에 `last_complete_line`. 마지막 줄 시간 > H 면 건너뜀.
   - `pods` 가 있고, 파드가 목록에 없고, 120초 넘게 조용하면 → **고아** (`orphans`). 꼬리가 있으면 `malformed` 에
     "unterminated last line of an orphaned file" 로 추가.
   - `pods` 가 있고, 파드가 목록에 있고, 마지막 줄 시간 < H 면 → `idle_log_files`.
4. **정책 적용**: `cfg.policy.apply(entries, context, h, key)` → `(processed, dropped, summary, rows)`.
5. **검사**: `lines_in = len(entries) + len(malformed)` 가 `processed + dropped + malformed` 와 다르면 `RuntimeError`.
6. **요약 보강**: §9.2 의 배치 필드를 `summary` 에 더한다. `pods` 가 None 이면 `orphans_moved`·`idle_log_files` 는 null.

결과: `{key, processed, malformed, summary, rows, orphans, corrupt}`.

## 13. 정책 — `AuditPolicy.apply(entries, context, h, key)`

1. `entries` 를 `(ts, file, line_no)` 로 정렬 — 평가 순서를 결정적으로.
2. `status_idx = access_status_index(context)`: 문맥 창의 액세스 줄 중 요청 ID 가 있고 파싱되는 것으로
   `requestId → [(시각, 상태), …]`.
3. **1차 패스 — 지속 키(persistent)**: ERROR/WARN 이 아닌 액세스 줄 중 상태 < 400 인 것의 리소스 키, 그리고 커밋 로그의
   리소스 키를 모은다. "이 리소스는 이 시간에 존재했다" 는 사실 — 오류 요청이 그 행에 붙을 수 있는지(§9) 를 순서와
   무관하게 정한다.
4. **2차 패스 — 판정**: 각 줄의 사본(`dict(rec)`)에 `_decide` → 참이면 `TRIMMED_FIELDS` 를 빼고
   `processed_doc`(= `event_id`, `log_hour` 추가), 거짓이면 `dropped += 1`.
5. `HourReport.rows(h, pods)` 로 요약과 행을 만든다.
6. 검사: `len(entries) = 적재 + dropped`, `dropped = access_counted + app_dropped_total + app_dropped_404`.
   어긋나면 `RuntimeError` (assert 가 아니다 — `python -O` 가 assert 를 지우므로).

**`_decide(rec, ts, rep, status_idx)`** — §8 표를 위에서부터:
```
redact_secret(rec)                                   * 자격증명 가드
is_access = loggerName == "io.quarkus.http.access-log"
parsed    = parse_access(rec) if is_access           정규식 %h %l %u %t "%r" %s %b → 필드 추가, 실패면 access_log_parse_error
if level in (ERROR, WARN):              keep         1
if not is_access:
    if logger == IcebergCatalog:        rep.count_commit(message)        2a (그리고 아래로 계속)
    if logger in APP_ALLOW:                                              2b
        rid = mdc.requestId;  없으면    keep
        st  = matching_status(status_idx, rid, ts)
        st None → held_orphan=true, held_orphans++, keep
        st 404  → app_dropped_404++, drop
        그 외   → keep
    rep.count_dropped(logger);          drop                             2c
rep.count_access(rec, parsed)                        먼저 세고 나중에 판정
404                          → counted_404++, access_counted++, drop     3′
상태 없음(파싱 실패) or ≥400 → errors_kept++, keep                       3
PUT/DELETE/PATCH             → keep                                      4
POST: /api/management/…      → keep;  그 밖 → counted_post++, access_counted++, drop   5
GET/HEAD                     → counted_read++, access_counted++, drop    6
그 외                        → keep                                      7
```

**`matching_status(idx, rid, t)`** — 같은 요청 ID 의 액세스 줄 중 **앱 줄과 같거나 뒤, 30초 이내**에서 가장 가까운 것의
상태. 없으면 **앞, 30초 이내**에서 가장 가까운 것. 둘 다 없으면 `None`.

**`HourReport`** — 한 시간의 카운터.
- `count_access`: `access_seen++`, `min/max_record_time` 갱신(문자열 비교 — 고정 형식·고정 오프셋이라 사전순 = 시간순).
  파싱 실패면 `parse_errors++` 로 끝. 아니면 `classify_path` 로 키·종류, `is_error = 상태 ≥ 400`,
  `create = (not is_error) or 키 ∈ persistent`; 여전히 거짓이고 롤 종류면 이미 행이 있거나 `role_keys_forced < 100`
  일 때 강제 생성. `resource(...)` 와 `principal(user)` 양쪽에 `bump`.
- `resource(key, kind, api, create)`: 있으면 그 행. `create` 가 거짓이면 `__errors__`. 실제 행이 500개면
  `resources_over++`, `other_keys` 에 키 추가(최대 500), `__other__`.
- `principal(user)`: 200개 넘으면 `principals_over++`, `__other__`.
- `bump(row, method, status, size, is_error)`: `requests++`; GET/HEAD → `reads`, 쓰기 메서드 → `writes`;
  오류면 `errors`, 5xx/4xx, 401·403 → `auth_denied`; `response_bytes += size`; 2xx 이고 크기 > 0 이면
  `last_read_bytes`/`last_write_bytes` 를 마지막 값으로.
- `count_commit(msg)`: `commit_key` 로 키를 만들고 `create=True` 로 행을 잡아 `commit_count/sum/min/max` 갱신.
  **요청 카운터는 건드리지 않는다** (커밋만 있는 행은 `requests: 0`).
- `count_dropped(logger)`: logger 별 카운트, 50종 넘으면 `__other__`.
- `rows(h, pods)`: 리소스(키 정렬; `requests > 0` 이거나 커밋이 있는 것만), principal(정렬, `last_*` 제외),
  app_dropped(정렬), 그리고 맨 앞에 요약. `distinct_resources` 는 `requests > 0` 인 리소스 수.

**`PassthroughPolicy`** — 모든 정상 줄을 그대로 적재하고 최소 요약만 낸다. 프레임워크 테스트와 원본 재생용이며
CronJob 은 쓰지 않는다.

## 14. 발행·정리·보존

- **`atomic_write(log_dir, dest, data)`**: `.tmp/<이름>.<pid>` 에 쓰고 flush + fsync → `os.replace(tmp, dest)` →
  디렉터리 fsync. `.tmp/` 가 같은 PVC 안에 있어야 `rename` 이 원자적이다.
- **`publish`**: malformed(있을 때) → processed(빈 시간도 빈 파일) → aggregated(요약에 `published_at` 을 넣고 요약 + 행).
- **`save_checkpoint`**: `.state/checkpoint.json` 을 같은 방식으로.
- **`housekeep_after(cfg, files, h, result)`**: 깨진 회전 파일 → `malformed/files/`; `roll` 이고 이름 시간 ≤ H →
  `done/<그 날짜>/`; 고아 → `done/<마지막 줄 날짜>/<이름>.<YYYY-MM-DD-HH>.orphan`. 모두 `move_unique`(같은 이름이면
  `.1` … 를 붙이고 `os.rename`). 이미 사라진 파일은 건너뛴다.
- **`retention(cfg, now)`**: 네 디렉터리를 아래에서부터 돌며 수정 시각이 3일 지난 파일을 지우고, 비게 된 하위
  디렉터리를 지운다 (§7 의 주의: `done/` 파일은 원래 수정 시각).

## 15. 체크포인트와 출력 형식

`.state/checkpoint.json`
```json
{
  "schema": "polaris-log-batch/1",
  "last_published": "20260928-10",
  "hours": {
    "20260928-10": {"published_at": "2026-09-28T11:03:01+09:00", "processed": 812, "malformed": 0,
                    "sources": [{"file": "polaris-benchmarks-polaris-…-bmt4t.log.2026-09-28-10.gz", "lines": 1904}]}
  }
}
```
- `processed-logs/H.jsonl`: 줄마다 §8.2 의 문서. `malformed/H.jsonl`: `{reason, file, line_no, raw}`.
- `aggregated-logs/H.jsonl`: 첫 줄 요약, 이어서 resource → principal → app_dropped 행.
- **표준 출력(Job 로그)**: 한 줄 JSON 이벤트 — `skipped`(락), `idle`, `deferred`, `dry-run`, `published`(요약 전체 +
  `moved`), `retention`.

## 16. 오류 처리·종료 코드·상수

| 상황 | 동작 | 종료 코드 |
|---|---|---|
| 다른 실행이 락을 잡음 | `skipped` 출력, 아무것도 안 함 | 0 |
| 파일도 체크포인트도 없음 | `idle` | 0 |
| 압축 중일 수 있는 `.gz` | 그 시간부터 중단(`deferred`), 보존 정리는 수행 | 0 |
| 오래된 깨진 `.gz` | 격리하고 계속 | 0 |
| Pod 목록 조회 실패 | 처리는 계속, 고아 이동 안 함, 요약 `pod_list_error` | 0 |
| 불변식 위반, 디스크 오류 등 예외 | 그 시간은 발행되지 않음(체크포인트 전), 트레이스백 | 1 → Job 실패, `backoffLimit: 1` 로 한 번 재시도 |

| 상수 | 값 | 의미 |
|---|---|---|
| `QUIET_SECONDS` | 120 | 이만큼 수정이 없으면 "지금 쓰는 중이 아니다" |
| `GRACE_SECONDS` | 60 | 시간 H 는 H+1:00 + 이것 이후 처리 |
| `HOLD_SECONDS` | 30 | 요청 ID 매칭 창(앞뒤), 문맥 창의 여유 |
| `MAX_HOURS_PER_RUN` | 72 | 한 실행의 따라잡기 상한 |
| `RETENTION_SECONDS` | 3일 | 보존 |
| `TAIL_BYTES` | 256 KB | 마지막 줄을 찾을 때 읽는 끝부분 |
| `REPORT_MAX_*` | 리소스 500, principal 200, 롤 강제 100, logger 50 | 행 상한 |

**CLI**: `--log-dir`(기본 `/deployments/logs`, env `LOG_DIR`) · `--pod-prefix`(기본 `benchmarks-polaris-`, env
`POD_PREFIX`) · `--selector`(env `POD_SELECTOR`) · `--no-pod-list`(API 없이 처리, 고아 이동 안 함) · `--now ISO`(재생·시험용
"지금") · `--dry-run`(계산하고 출력만, 아무것도 쓰지 않음, 체크포인트 불변).

---

# 3부 — 배포·운영

## 17. 빌드와 배포

```bash
kubectl config current-context                     # orbstack
docker build -t polaris-log-batch:0.1.0 images/polaris-log-batch
helm lint charts/polaris-log-batch
helm upgrade --install polaris-log-batch ./charts/polaris-log-batch \
  -f charts/polaris-log-batch/values.yaml -n datahub-hynix --dry-run=client --debug
helm upgrade --install polaris-log-batch ./charts/polaris-log-batch \
  -f charts/polaris-log-batch/values.yaml -n datahub-hynix
kubectl -n datahub-hynix create job --from=cronjob/polaris-log-batch log-batch-manual-1   # 수동 1회
kubectl -n datahub-hynix logs -f job/log-batch-manual-1
```

- **이미지**: `python:3.11-slim` + 스크립트, `USER 10000:10001`. OrbStack 은 로컬 Docker 이미지를 그대로 쓰므로
  `image.pullPolicy: Never`. 운영은 Jenkins 가 사내 레지스트리로 올리고 `repository`/`IfNotPresent` 로 바꾼다.
- **차트 `charts/polaris-log-batch/`**: ServiceAccount, Role(`pods` `get`/`list`, 네임스페이스 한정), RoleBinding,
  CronJob(`3 * * * *`, `timeZone: Asia/Seoul`, `Forbid`, `activeDeadlineSeconds 3000`, `backoffLimit 1`,
  `readOnlyRootFilesystem`, uid/gid 10000/10001).
- **values 의 `polaris:` 는 Polaris 릴리스와 맞아야 한다** — 이 차트는 Polaris 값을 읽을 수 없다:
  `logsClaim: polaris-logs-pvc`, `logsDir: /deployments/logs`, `podPrefix: benchmarks-polaris-`,
  `podSelector: app.kubernetes.io/instance=benchmarks-polaris,app.kubernetes.io/name=benchmarks-polaris`.
- **Job 파드는 Polaris 의 selector 라벨을 달지 않는다** — 달면 Polaris Service 가 카탈로그 트래픽을 Job 파드로 보낸다.

## 18. 검증

| 무엇 | 결과 |
|---|---|
| 파드별 파일 / 공유 파일 손실 | §2.1 — 파드별 0건, 공유 44~61% 유실 (step15, OrbStack) |
| 시간 회전·KST·게으른 회전·고아 | 실제 파드에서 확인 (`-18.gz`, `-22.gz`, `2tklb`, 2026-09-27) |
| 프레임워크 테스트 26 | 나노초 경계, 경계 스큐, 쓰는 중인 줄, 읽지 못한 줄, 고아(파드 없음/있음/조용하지 않음/API 실패/잘린 줄), 크래시 후 재실행, 유휴 파드의 늦은 회전, 손상 .gz(미룸/격리), 빈 시간, 따라잡기 상한, 여유 시간, 락, dry-run, 보존, `2tklb` 모양 |
| 정책 테스트 14 | 규칙 1–7, 필드 정리·event_id, 404 동반 폐기, 액세스 뒤의 앱 줄, 보류 고아, 요청 ID 없음, 시간 경계를 넘는 짝, ERROR/WARN, 커밋 수확·중첩 네임스페이스, 오류의 행 귀속, 거부된 grant 의 롤 행, principal 상한, 자격증명 가드, 불변식 |
| **Lua 와 동등성** | step16: 같은 입력을 실제 Lua 필터(LuaJIT, `pip install lupa`)와 배치에 넣어 비교 — **시드 5개 × 약 5,300줄, 적재 문서와 모든 카운터 일치**. 규칙 하나를 일부러 깨면 차이를 잡는다 |

실행: `PYTHONDONTWRITEBYTECODE=1 pytest tests/test_polaris_log_batch.py tests/test_polaris_log_policy.py`,
`python3 logging/scripts/step16-batch-lua-parity.py [--seed N --n N | --file … --hour YYYYMMDD-HH]`.

## 19. 남은 일과 알려진 제약

- **첫 배포와 첫 실행** — 이미지 빌드, 차트 lint/렌더/설치, 수동 Job 1회, 결과 확인
  (`logging/HANDOFF-polaris-log-batch-2026-09-28.md`).
- **첫 실행은 따라잡기다** — 체크포인트가 없으므로 디스크의 가장 이른 줄(09-27 22시경)부터 최대 72시간을 처리하고,
  회전 파일과 step15 시험으로 생긴 고아 파일들을 `done/` 으로 옮긴다.
- **운영 클러스터 저장소** — 여러 노드에서는 ReadWriteOnce PVC 가 한 노드에만 붙는다 → RWX 스토리지 또는 Polaris 파드와
  Job 을 한 노드에 고정(`affinity`)해야 한다.
- **메모리** — 한 시간 분량의 적재 대상 줄을 메모리에 올려 판정한다. 운영 트래픽의 시간당 크기로 `resources.limits.memory`
  를 정할 것.
- **실제 로그로 동등성 재확인** — step16 `--file` 로. 실제 트래픽에서는 §9.1 "오류 요청의 행" 차이가 나타날 수 있다(의도).
- **관측팀 인계** — 디렉터리·파일 이름·완료 신호(aggregated 파일)·`event_id` → `_id`·3일 수집 기한을 계약으로 넘길 것.
- **Fluent Bit tier 2/3 와 병행 비교 후 정리** — 로컬에서만 가능 (운영 Fluent Bit 은 우리 소관이 아니다).
