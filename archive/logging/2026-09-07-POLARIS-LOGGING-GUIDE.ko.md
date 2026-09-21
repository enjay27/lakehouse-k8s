> **과거 문서 (2026-09-16 표시).** 2026-09-07 기준 (VictoriaLogs 시기) 상태를 기술한다. 현재 파이프라인(Fluent Bit DaemonSet → OpenSearch, 정책 v5)은 `SPEC-polaris-audit-logging.ko.md`, 문서 현황은 `README.md`.

# Polaris 로깅 파이프라인 완전 가이드

**대상**: 이 플랫폼을 처음 맡는 엔지니어, 그리고 무엇이 보장되고 무엇이 보장되지 않는지 알아야 하는 관리자
**기준 시점**: 2026-09-07
**성격**: 설계 문서(`2026-09-03-polaris-logging-architecture-spec.md`)가 *의도*를 기술한다면, 이 문서는 **실제로 배포되어 돌아가는 상태**를 기술한다. 둘이 다른 곳은 다르다고 적었다.

---

## 0. 이 문서를 읽는 법

모든 설정값에는 검증 등급이 붙어 있다.

| 표기 | 의미 |
|---|---|
| **[검증됨]** | 실행 중인 객체 또는 저장된 로그에서 직접 확인함 |
| **[미검증]** | 저장소의 파일 기준. 실제로 적용되어 있는지는 확인하지 않음 |
| **[불일치]** | 파일과 실제 동작이 다르다고 알려진 항목 |

**왜 이런 표기가 필요한가.** 이 저장소에서는 `postgresql:` 블록 전체가 잘못된 들여쓰기 위치에 있어 몇 달 동안 서브차트 기본값이 서비스되고 있었고, 아무도 알아채지 못했다. values 파일은 *의도의 진술*이고, 그것이 *실제로 적용되어 있는지*는 별개의 사실이다. 그래서 이 저장소의 제1원칙은 이렇다.

> **values 파일을 읽어서 설정을 확인하지 말 것. 실행 중인 객체를 조회해서 차트 기본값과 비교할 것.**
> 기본값과 같은 값은 증거가 아니다 — 적용된 적 없는 블록과 구별되지 않는다.

이 문서 자체도 그 함정에 빠질 수 있다. 값을 그대로 옮겨 적으면 문서는 또 하나의 의도 산출물이 된다. 표기는 그것을 막기 위한 것이다.

---

## 1. 이 파이프라인이 답하는 질문

> **"내일 이 엔드포인트에서 문제가 생기면, 그 기록이 남아 있는가?"**

로그 수집이 목적이 아니라 **감사 가능성(auditability)** 이 목적이다. 정책 v3는 그 질문에 답하기 위해 한 가지를 명시적으로 포기했다.

| 지킨 것 | 포기한 것 |
|---|---|
| 모든 에러(4xx/5xx)는 상한 없이 전부 저장 | 성공한 읽기는 개별 레코드로 남지 않음 |
| 모든 변경(PUT/DELETE/PATCH)은 전부 저장 | 개별 읽기의 시각·빈도는 집계 안에만 존재 |
| `/api/management/` 하위의 모든 POST는 전부 저장 | 캐시가 따뜻한 반복 읽기는 **끝에서 끝까지 보이지 않음** |

마지막 줄이 중요하다. **[검증됨]** 동일한 `load_table` 3회 중 첫 번째만 애플리케이션 로그 한 줄을 남기고, 나머지 두 번은 아무것도 남기지 않았다. "counted된 호출은 애플리케이션 로그로 추적할 수 있다"고 가정하면 틀린다.

v2에서는 관리 API의 POST가 전부 버려졌고, 그래서 **자격증명 리셋(`POST /principals/{p}/reset`)이 아무 흔적도 남기지 않았다.** v3가 닫은 구멍이 이것이다.

---

## 2. 전체 아키텍처

### 2.1 데이터 흐름

```
Apache Polaris (Quarkus, JDK21)
  │  한 줄에 JSON 하나 (NDJSON)
  ▼
/deployments/logs/polaris.log        ← PVC: polaris-shared-logs-pvc
  │                                    (Polaris는 read-write, shipper는 read-only)
  ▼
fb-polaris-shipper (Fluent Bit Deployment, ns: datahub-hynix)
  │
  ├─ [INPUT tail]        polaris.log 를 따라가며 읽음        → tag: polaris.vlogs
  ├─ [INPUT dummy]       5초마다 틱                          → tag: polaris.report
  │
  ├─ [FILTER modify]           message→_msg, timestamp→_time, app=polaris 추가
  ├─ [FILTER lua]              polaris_access_log   — 접근 로그 한 줄을 필드로 분해
  ├─ [FILTER lua]              polaris_noise_filter — 무엇을 저장할지 결정 ★핵심
  ├─ [FILTER record_modifier]  processName / loggerClassName / processId 제거
  │
  ▼ [OUTPUT http]  json_lines
VictoriaLogs (ns: logging, 9428) /insert/jsonline
```

**핵심은 세 번째 필터 하나다.** 나머지는 그것을 위한 준비와 정리다.

### 2.2 Fluent Bit이 두 개인 이유 — 반드시 먼저 읽을 것

이 클러스터에는 Fluent Bit 릴리스가 **두 개** 있고, 둘 다 `datahub-hynix` 네임스페이스에 있다. 중복이 아니라 의도된 구성이다.

| 릴리스 | 형태 | 수집 대상 | 목적지 | values |
|---|---|---|---|---|
| `fb-polaris-shipper` | **Deployment** | Polaris 로그 PVC | **VictoriaLogs** | `logging/fb-values.yaml` |
| (DaemonSet 릴리스) | DaemonSet | `/var/log/containers/*.log` | **OpenSearch** (Docker, 클러스터 외부) | `fluent-bit/values.yaml` |

**이 문서는 앞의 것만 다룬다.** OpenSearch에는 있는데 VictoriaLogs에는 없는 로그가 보인다면, 그것은 DaemonSet이 한 일이지 이 파이프라인의 결함이 아니다.

### 2.3 컴포넌트 인벤토리

| 항목 | 값 | 등급 |
|---|---|---|
| 클러스터 컨텍스트 | `orbstack` (개인 OrbStack 단일 노드) | [검증됨] |
| Polaris 네임스페이스 | `datahub-hynix` | [검증됨] |
| 로그 싱크 네임스페이스 | `logging` | [검증됨] |
| Polaris 버전 / 관리 포트 | v1.3.0-incubating / **8182** (상위 문서 기본값 8282 아님) | [미검증] |
| Fluent Bit 차트 / 앱 | `fluent-bit-0.58.1` / **5.1.1** | [미검증] |
| VictoriaLogs | `logging` 네임스페이스, 포트 9428 | [검증됨] |
| VictoriaLogs 접근 | LoadBalancer `192.168.139.2:9428` | [검증됨] |
| Polaris 로그 PVC | `polaris-shared-logs-pvc` | [검증됨] |

의존 순서는 단방향이며 이를 어기면 부팅되지 않는다: **MinIO → PostgreSQL → Polaris → 나머지 전부.**

---

## 3. Polaris 설정 — 로깅에 필요한 변경

### 3.1 필수 항목은 네 가지다

1. **파일로 JSON을 쓸 것.** 콘솔이 아니라 파일이어야 한다 — 콘솔은 DaemonSet이 가져가고, 그쪽은 이 파이프라인이 아니다.
2. **그 파일이 공유 PVC 위에 있을 것.** shipper가 같은 볼륨을 read-only로 마운트한다.
3. **Quarkus HTTP access log가 켜져 있을 것.** 이것이 없으면 파이프라인이 셀 것이 없다.
4. **MDC `requestId`가 전파될 것.** 하나의 요청이 남긴 여러 줄을 이어 붙이는 유일한 수단이다.

### 3.2 실제 설정 (`polaris/values.yaml`)

```yaml
# 환경변수 — Quarkus 3.29.4에서 도입된 키
extraEnv:
  - name: QUARKUS_LOG_CONSOLE_JSON_ENABLED
    value: "true"
  - name: QUARKUS_LOG_FILE_JSON_ENABLED
    value: "true"
  - name: QUARKUS_LOG_FILE_JSON_PRETTY_PRINT
    value: "false"

# 공유 볼륨 — shipper가 읽는 바로 그 PVC
extraVolumes:
  - name: polaris-log-volume
    persistentVolumeClaim:
      claimName: polaris-shared-logs-pvc
extraVolumeMounts:
  - name: polaris-log-volume
    mountPath: /deployments/logs        # ← Polaris 쪽 경로

logging:
  level: INFO
  requestIdHeaderName: Polaris-Request-Id   # ← MDC requestId 의 출처
  file:
    enabled: false                          # ← [불일치] 3.6 참고
    json: false                             # ← [불일치] 3.6 참고
    logsDir: /deployments/logs
    fileName: polaris.log
    rotation:
      maxFileSize: 10Mi
      maxBackupIndex: 5
```

마운트 경로가 양쪽에서 다르다는 점에 유의한다. **Polaris는 `/deployments/logs`, shipper는 같은 PVC를 `/logs`로 마운트한다.** 서로 다른 컨테이너이므로 문제는 없지만, 경로만 보고 다른 파일이라고 오해하기 쉽다.

### 3.3 access log 패턴 — 이 저장소 어디에도 없다 ⚠

Lua 파서는 정확히 이 패턴을 기대한다.

```
%h %l %u %t "%r" %s %b
```
```
192.168.194.1 - root [03/Sep/2026:06:37:47 +0000] "DELETE /api/... HTTP/1.1" 404 133
```

그런데 **`quarkus.http.access-log.pattern`을 설정하는 곳이 이 저장소에 없다.** `polaris/values.yaml`에는 카테고리 레벨(`io.quarkus.http.access-log: INFO`)만 있다. 즉 현재 파서는 **Polaris/Quarkus의 기본 패턴에 의존하고 있으며, 업그레이드로 그 기본값이 바뀌면 파싱이 조용히 깨진다.**

설계 문서 §3.1은 `"%h %u %t \"%r\" %s %b"`(`%l` 없음)를 제시하는데, 파서는 `%l`을 요구한다. **설계 문서를 그대로 적용하면 모든 접근 로그가 파싱에 실패한다.**

유일한 탐지 수단은 이것이다. 정기적으로 확인할 것:

```
app:polaris access_log_parse_error:true | stats count()
```

파서는 읽지 못한 줄을 **버리지 않고 태그만 붙여 저장한다.** 조용한 실패가 없다는 뜻이다.

### 3.4 카테고리 로그 레벨 — 끄지 말아야 할 것

```yaml
logging:
  categories:
    org.apache.polaris.persistence.relational.jdbc.DatasourceOperations: DEBUG   # ★
    org.apache.polaris.service.auth: DEBUG                # 401 조사용
    org.apache.polaris.service.catalog: DEBUG             # 403 조사용
    org.apache.polaris.core.persistence: DEBUG            # 500 entity_version 조사용
    org.apache.polaris.service.storage: DEBUG             # NPE 조사용
    org.apache.polaris.service.context.ServiceProducers: "OFF"   # 자격증명 노출 방지
    io.smallrye.config: "OFF"                                    # 자격증명 노출 방지
```

**`DatasourceOperations`를 DEBUG에서 내리지 말 것.** 저장 용량의 대부분을 차지하는 것이 이 로거이지만(§8.2), `polaris-learning` 스위트가 이 로거의 DEBUG 출력에 의존한다. 용량이 문제라면 **레벨을 낮추는 것이 아니라 경로를 분리해야 한다.**

`ServiceProducers`와 `io.smallrye.config`가 `OFF`인 것은 성능이 아니라 **보안** 때문이다. 켜면 설정값이 로그로 나가고 거기에는 자격증명이 들어 있다.

### 3.5 적용 여부를 확인하는 방법

values 파일을 다시 읽는 것은 확인이 아니다.

```bash
kubectl config current-context      # 반드시 orbstack 이어야 한다

# 1) 파일이 실제로 쓰이고 있는가
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- \
  ls -la /deployments/logs/polaris.log

# 2) 그 내용이 JSON 한 줄인가
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- \
  tail -1 /deployments/logs/polaris.log

# 3) access log가 실제로 나오고 있는가
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- \
  grep -c 'io.quarkus.http.access-log' /deployments/logs/polaris.log

# 4) 실행 중인 파드가 어떤 환경변수를 갖고 있는가
kubectl -n datahub-hynix get deploy benchmarks-polaris -o yaml | grep -A2 QUARKUS_LOG
```

### 3.6 알려진 불일치 ⚠

**`logging.file.enabled: false`인데 파일 로깅이 동작한다.** `active-issues.md` #11에 기록된, **설명되지 않았고 추적하지 않기로 한** 항목이다. 환경변수 쪽(`QUARKUS_LOG_FILE_JSON_ENABLED=true`)이 실제로 효력을 갖는 것으로 보이지만 확정되지 않았다.

이것을 "정리"하려는 시도(#12)는 **철회되었다.** 이유는 이 저장소의 원칙 그대로다 — **한 번도 실행된 적 없는 설정을 되살리는 것은 수정이 아니라 변경이다.** 지금 동작하는 것을 건드리면 무엇이 깨질지 알 수 없다.

또한 `polaris/values.yaml` 전반이 실행 중인 Polaris를 정확히 기술하지 못한다(#5). **로깅과 무관한 값을 이 파일에서 읽어 신뢰하지 말 것.**

그리고 이것은 표준 제약이다: **Polaris는 변경하지 않는다.** 잘 돌아가고 있고 계속 배포되는 컴포넌트이기 때문이다. `%D`(요청 소요시간) 추가처럼 명백히 유용한 변경도 이 규칙 뒤에 보류되어 있다.

---

## 4. Fluent Bit shipper (`logging/fb-values.yaml`)

### 4.1 파일 구조

```
kind: Deployment              # DaemonSet 아님 — 로그가 PVC 위에 있으므로 노드마다 돌 필요가 없다
replicaCount: 1               # ★ 1을 유지할 것. 4.2 참고
resources: {...}
extraVolumes / extraVolumeMounts
luaScripts:                   # ← 약 550줄. 정책과 리포트가 전부 여기 있다
config:
  service / inputs / filters / outputs
```

`luaScripts` 블록이 **스크립트의 유일한 정본**이다. 차트가 이것을 ConfigMap으로 렌더링해 `/fluent-bit/scripts/`에 마운트한다. 테스트도 이 파일에서 Lua를 추출해 실행하므로, **테스트가 배포된 것과 어긋날 수 없다.**

```bash
python3 logging/scripts/test-polaris-filters.py      # 60/60
```

### 4.2 볼륨 — 두 개, 그리고 각각의 함정

```yaml
extraVolumes:
  - name: polaris-logs
    persistentVolumeClaim:
      claimName: polaris-shared-logs-pvc
  - name: flb-storage
    emptyDir:
      sizeLimit: 2Gi

extraVolumeMounts:
  - name: polaris-logs
    mountPath: /logs
    readOnly: true            # ← 로그 PVC는 읽기 전용
  - name: flb-storage
    mountPath: /var/log/flb-storage
```

**로그 PVC가 read-only이므로 tail 오프셋 DB와 디스크 버퍼는 거기에 둘 수 없다.** 그래서 `flb-storage` emptyDir이 따로 있다.

⚠ **emptyDir은 컨테이너 재시작(크래시, OOM)은 견디지만 파드 교체는 견디지 못한다. 그리고 `helm upgrade`는 파드를 교체한다.** 새 파드에서는 DB가 비어 있고 `Read_from_Head true`가 파일 전체를 다시 읽어 재전송하며, **VictoriaLogs는 ingest 시점에 중복 제거를 하지 않는다.** 즉 `helm upgrade` 한 번이 로그 전체를 중복시킬 수 있다.

이것을 없애려면 작은 PVC로 바꾼다 (roadmap #2, 아직 적용 안 됨):

```bash
kubectl -n datahub-hynix create -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: fb-polaris-shipper-state}
spec:
  accessModes: [ReadWriteOnce]
  resources: {requests: {storage: 1Gi}}
EOF
# 그 다음 fb-values.yaml 에서:  persistentVolumeClaim: {claimName: fb-polaris-shipper-state}
```

**`replicaCount`는 1이어야 한다.** Lua 필터의 상태(윈도 카운터)는 **필터 인스턴스별 메모리**에 있다. 레플리카를 늘리면 각자 자기 리포트를 내보내고 `report_seq`가 파드마다 따로 흐른다.

### 4.3 INPUT — 두 개

```ini
[INPUT]
    Name              tail
    Path              /logs/polaris.log
    Tag               polaris.vlogs
    Read_from_Head    true
    Parser            json
    Buffer_Chunk_Size 256k
    Buffer_Max_Size   10MB
    Skip_Long_Lines   On          # ★ Off면 긴 줄에서 tail이 "멈춘다" — 스택 트레이스가 긴 줄이다
    DB                /var/log/flb-storage/polaris_tail.db
    DB.sync           normal
    Refresh_Interval  5
    Rotate_Wait       10          # 로테이션된 inode를 마저 읽을 시간
    storage.type      filesystem

[INPUT]
    Name              dummy
    Alias             polaris_report_tick
    Tag               polaris.report
    Dummy             {"tick":"polaris-report"}
    Rate              1
    Interval_Sec      5           # ★ 임시값. 4.8 참고
```

`Skip_Long_Lines On`은 사고에서 배운 값이다. **`Off`는 "긴 줄을 버린다"가 아니라 "그 파일에 대한 tail이 정지하고 계속 정지해 있다"는 뜻이다.**

두 번째 INPUT은 **로그 데이터를 나르지 않는다.** 윈도가 넘어갈 때 필터가 이 틱을 리포트로 *치환*하고, 아니면 버린다.

> **틱 주기는 리포트 주기가 아니다.** 리포트 주기는 Lua 안의 `WINDOW_SECONDS`이며 벽시계 격자에 정렬된다. 틱은 경계를 "제때 알아차릴 만큼만" 자주 오면 되고, **반드시 `WINDOW_SECONDS`보다 충분히 작아야 한다.** 틱 == 윈도이면 지터 때문에 경계가 그냥 지나갈 수 있다.

### 4.4 FILTER 체인 — 순서가 계약이다

| # | 필터 | Alias | Match | 하는 일 |
|---|---|---|---|---|
| 1 | `modify` | `polaris_key_rename` | `polaris.vlogs` | `message→_msg`, `timestamp→_time`, `app=polaris` |
| 2 | `lua` | `polaris_access_log` | `polaris.vlogs` | 접근 로그 한 줄을 타입 있는 필드로 분해 |
| 3 | `lua` | **`polaris_noise_filter`** | **`polaris.*`** | 저장 여부 결정 + 전수 집계 ★ |
| 4 | `record_modifier` | `polaris_field_trim` | `polaris.vlogs` | 무가치한 필드 제거 |

세 가지가 의도적이다.

- **3번만 `polaris.*`다.** 리포트 틱이 이 인스턴스에 닿아야 하기 때문이다. Lua 상태는 인스턴스별이고 카운터는 여기에 산다. 반대로 1·2번이 `polaris.vlogs`인 덕분에 **틱은 `app=polaris`를 얻지 않고 접근 로그 파서 근처에도 가지 않는다.**
- **`Alias`가 없으면 `fluentbit_filter_drop_records_total`을 필터별로 귀속시킬 수 없다.** `lua` 필터 두 개는 메트릭에서 구별되지 않는다.
- **3번이 4번보다 먼저다.** 곧 버릴 레코드를 다듬는 데 비용을 쓰지 않는다.

`type_int_key`는 두 필터 모두에 있다. 없으면 Fluent Bit이 숫자를 double로 인코딩하고 VictoriaLogs가 `"404.0"`으로 저장해서 **숫자 LogsQL 필터가 조용히 아무것도 못 찾는다.**

### 4.5 보존 정책 v3 — 규칙표

**엄격한 순서, 첫 매치 승리.**

| # | 조건 | 결과 |
|---|---|---|
| 0 | 태그가 `polaris.report` | **플러시 리포트**로 치환 |
| 1 | `level`이 ERROR 또는 WARN | **keep** |
| 2 | 접근 로그 레코드가 아님 | **keep** (그대로 통과) |
| — | *여기서 모든 접근 로그 레코드가 **집계**된다 — 어떤 판단보다 먼저* | |
| 3 | `http_status >= 400`, 또는 파싱 실패 | **keep — 전부, 상한 없음** |
| 4 | PUT / DELETE / PATCH | **keep** |
| 5 | `/api/management/` 하위의 POST | **keep**. 그 외 POST는 **counted only** |
| 6 | GET / HEAD, 2xx | **counted only** |
| 7 | 그 외 전부 | **keep** |

**"먼저 세고, 나중에 판단한다"**가 이 설계의 핵심이다. 억제될 수 있는 모든 것이 카운터에 잡혀야 하며, 그렇지 않으면 억제된 레코드는 요약되는 게 아니라 **분실된다**.

주의할 귀결 두 가지:

- **일 단위 중복 제거는 없다.** dedup 키도, KST 버킷도, 상한도, 파드별 상태도 없다. 따라서 shipper가 재시작해도 잃을 상태가 없다.
- **첫 매치 승리이므로 규칙 3이 규칙 5보다 먼저다.** 403을 받은 관리 POST는 규칙 5가 무엇을 하든 규칙 3으로 저장된다. 규칙 5의 효과를 측정하려면 **2xx인 관리 POST만** 세야 한다.

### 4.6 OUTPUT

```ini
[OUTPUT]
    Name          http
    Match         polaris.*
    Host          vlsingle-victoria-logs-single-server.logging.svc.cluster.local
    Port          9428
    URI           /insert/jsonline?_msg_field=_msg&_time_field=_time&_stream_fields=app,level
    Format        json_lines
    Header        Content-Type application/json
    json_date_key false          # Fluent Bit이 _time과 중복되는 date 키를 붙이는 것을 막음
    Retry_Limit              5
    storage.total_limit_size 1G
```

`_stream_fields=app,level`이므로 리포트는 **자기 스트림**(`{app="polaris-shipper-report", level="REPORT"}`)에 착지한다. `app:polaris` 쿼리는 영향받지 않는다.

`[SERVICE]`의 디스크 버퍼링과 합쳐져, **VictoriaLogs가 재시작하거나 네트워크가 멈춰도 큐가 디스크에 쌓였다가 나중에 빠진다.**

```ini
[SERVICE]
    Flush         1
    HTTP_Server   On
    HTTP_Port     2020            # 메트릭
    storage.path              /var/log/flb-storage/
    storage.sync              normal
    storage.max_chunks_up     64
    storage.backlog.mem_limit 32M
```

### 4.7 helm 명령

```bash
kubectl config current-context          # orbstack 확인 — 변경 전 필수

# 1) 렌더링 먼저. `helm lint`는 렌더링이 아니다.
helm upgrade --install fb-polaris-shipper fluent/fluent-bit --version 0.58.1 \
  -n datahub-hynix -f logging/fb-values.yaml --dry-run --debug > /tmp/render.txt

# 2) values가 템플릿에 실제로 도달했는지 확인 — 이 검사가 #13을 잡았을 검사다
grep -c RESOURCE_PATTERNS           /tmp/render.txt   # >= 1  (v3 Lua 존재)
grep -c 'MGMT_PREFIX'               /tmp/render.txt   # >= 1  (규칙 5 분기)
grep -c 'Name              dummy'   /tmp/render.txt   # 1     (리포트 틱)
grep -c 'Match         polaris\.\*'  /tmp/render.txt   # 2     (noise filter + output)
grep -c type_int_key                /tmp/render.txt   # 2
grep -c DEDUP_MAX_KEYS              /tmp/render.txt   # 0     (v2 잔재 없음)
# 앞의 다섯 중 하나라도 0이거나 마지막이 0이 아니면 중단한다.

# 3) 업그레이드
helm upgrade --install fb-polaris-shipper fluent/fluent-bit --version 0.58.1 \
  -n datahub-hynix -f logging/fb-values.yaml

kubectl -n datahub-hynix rollout status deploy/fb-polaris-shipper
kubectl -n datahub-hynix logs deploy/fb-polaris-shipper | head -60   # ★ 제일 먼저 읽을 것

# 실제로 배포된 스크립트가 파일과 같은지 — 이것이 유일한 확인 방법이다
kubectl -n datahub-hynix get configmap fb-polaris-shipper-fluent-bit \
  -o jsonpath='{.data.polaris_access_log\.lua}' | shasum -a 256
```

Lua 문법 오류나 거부된 `type_int_key` 줄은 **파드 로그에 나타난다.** 파드가 크래시 루프에 빠지거나, 더 나쁘게는 **필터가 무력화된 채로 돌아간다.** 무력화된 필터는 바깥에서 보면 성공처럼 보인다 — 그것이 #13이었다.

### 4.8 지금 살아 있는 임시 설정과 복귀 절차 ⚠

**[검증됨] 아래 두 값은 임시이며 아직 되돌리지 않았다.**

| 항목 | 정상 상태 | 현재 | 이유 |
|---|---|---|---|
| `WINDOW_SECONDS` (Lua) | 1800 | **30** | 커버리지 실행이 ~90분이 아니라 ~2분에 세 경계를 넘도록 |
| `Interval_Sec` (dummy INPUT) | 30 | **5** | 윈도당 6틱 — 지터로 경계를 놓치지 않도록 |

**반드시 함께 되돌린다.** 노트북도 테스트도 이 숫자를 하드코딩하지 않으며, `Policy.window_seconds` / `Policy.tick_seconds`가 배포된 파일에서 읽어 온다.

복귀 시 같이 실을 것: **요약 `_msg`에 `resources_other` / `resources_other_distinct` 추가.** 현재 두 필드는 JSON에는 있지만 사람이 읽는 `_msg` 문장에는 없다 (**[검증됨]**).

그때까지 저장소 파일은 배포된 ConfigMap과 **바이트 단위로 동일하게** 유지한다. 노트북의 게이트가 의미를 갖는 근거가 그것이다.

---

## 5. VictoriaLogs (`logging/victoria-values.yaml`)

### 5.1 values 전문

```yaml
server:
  enabled: true
  retentionPeriod: "30d"
  persistentVolume:
    enabled: true
    size: 50Gi
    accessModes:
      - ReadWriteOnce
  resources:
    requests: {cpu: "500m", memory: "1Gi"}
    limits:   {cpu: "2000m", memory: "4Gi"}
  service:
    enabled: true
    type: LoadBalancer          # ← 인증 없이 ingest와 query가 모두 열린다
    servicePort: 9428
  extraArgs:
    memory.allowedPercent: "60"
    http.maxGracefulShutdownDuration: "15s"
  livenessProbe:  {initialDelaySeconds: 15, periodSeconds: 10, timeoutSeconds: 5, failureThreshold: 3}
  readinessProbe: {initialDelaySeconds: 5,  periodSeconds: 5,  timeoutSeconds: 5, failureThreshold: 3}
  ingress:
    enabled: false
```

### 5.2 helm 명령

서비스 이름이 `vlsingle-victoria-logs-single-server`이므로 **릴리스 이름은 `vlsingle`이다.**

```bash
helm -n logging upgrade --install vlsingle <repo>/victoria-logs-single \
  -f logging/victoria-values.yaml --dry-run --debug
helm -n logging upgrade --install vlsingle <repo>/victoria-logs-single \
  -f logging/victoria-values.yaml
```

⚠ **[미검증]** 저장소에 VictoriaLogs 설치 명령이 기록된 곳이 없다. 차트 저장소 별칭(`<repo>`)과 차트 버전은 실제 릴리스에서 확인해야 한다:

```bash
helm -n logging list
helm -n logging get metadata vlsingle
```

이것은 이 가이드가 채우지 못한 공백이며, 다음에 이 릴리스를 만질 때 명령을 런북에 남길 것.

### 5.3 접근 경로

```bash
# 1) LoadBalancer (권장)
V=http://192.168.139.2:9428

# 2) port-forward
kubectl -n logging port-forward svc/vlsingle-victoria-logs-single-server 9428:9428
V=http://localhost:9428

# VM-UI (브라우저)
$V/select/vmui
```

### 5.4 알려진 위험 ⚠

- **`retention.maxDiskSpaceUsageBytes`가 없다.** 전역 보존 기간 하나뿐이고 디스크 상한이 없다. `persistence.size: 50Gi`는 **지금 아니면 못 바꾸는** 값이다 (#7).
- **9428이 인증 없는 LoadBalancer다.** ingest와 query 모두 열려 있다.
- **v3 이후 성공한 읽기는 집계로만 존재한다.** 즉 리포트 스트림의 보존 정책이 예전보다 훨씬 중요해졌다. 지금은 로그와 같은 전역 보존을 공유한다.

---

## 6. 스키마 레퍼런스

VictoriaLogs에는 **세 종류의 레코드**가 들어간다.

| 스트림 | 무엇 |
|---|---|
| `{app="polaris", ...}` | 접근 로그 레코드 (파싱된 필드가 붙음) |
| `{app="polaris", ...}` | 애플리케이션 로그 레코드 (규칙 2로 그대로 통과) |
| `{app="polaris-shipper-report", level="REPORT"}` | 플러시 리포트 3종 |

### 6.1 접근 로그 레코드

`polaris_access_log` 필터가 `_msg` 한 줄을 분해해 붙이는 필드다. `_msg`는 **지우지 않는다** — 파싱이 틀렸을 때 읽어야 할 원문이다.

| 필드 | 타입 | 예시 |
|---|---|---|
| `client_ip` | string | `192.168.194.1` |
| `user_principal_name` | string | `root`, `nb_1788760757_denied`, `-` |
| `http_method` | string | `GET`, `POST`, `DELETE` |
| `api_path` | string | `/api/catalog/v1/cat/namespaces/probe_ns/tables/probe_tbl` |
| `http_status` | **int** | `403` |
| `response_size` | **int** | `133` |
| `access_log_parse_error` | bool | 파싱 실패 시에만 존재 |

두 가지를 기억할 것.

- **필드 이름은 `api_path`이지 `path`가 아니다.** `path`로 질의하면 아무것도 나오지 않는다.
- **`%b`가 `-`인 경우는 0바이트이지 "모름"이 아니다.** CLF 규약이며 파서가 0으로 넣는다.
- OAuth 토큰 교환은 principal이 **`-`** 로 기록된다. 아직 인증되지 않았으므로 `%u`가 대시를 쓴다.

### 6.2 애플리케이션 로그 레코드 — 스택 트레이스는 평탄화된다

Quarkus는 예외를 **구조화된 객체**로 쓰고, **VictoriaLogs가 중첩 객체를 평탄화한다.** 따라서 저장된 필드는 이렇다.

```
exception.exceptionType     예: java.lang.NullPointerException
exception.message           예: grantee_not_found: grantee={}, [...]
exception.frames            약 60개 프레임의 배열
exception.refId
```

> ⚠ **`exception`으로 질의하면 아무것도 찾지 못한다. 반드시 `exception.*`로 질의할 것.**
> 이것 때문에 "스택 트레이스가 살아남지 않는다"는 잘못된 결론이 세 번의 실행에 걸쳐 유지됐다. `exception` 검색과 `grep -c stackTrace`가 **서로 일치했기 때문에** 확증처럼 보였지만, 둘 다 이 빌드가 쓰지 않는 이름을 찾고 있었다. **두 검색이 일치한다는 것은, 가정을 공유하고 있다면 확증이 아니다.**

**[검증됨]** 실행 `1788760757`에서 WARN/ERROR 레코드 **8건 중 8건**이 예외 페이로드를 갖고 있었다.

#### `IcebergExceptionMapper`는 두 층위를 내보낸다 ★

이 로거 하나가 **서로 다른 두 종류의 줄**을 만든다. 레벨이 그 구분이다.

| `level` | `_msg` | 대상 | 무엇이 들어 있나 |
|---|---|---|---|
| `INFO` | `Handling runtimeException <실제 사유>` | **매핑된 4xx 전부** (404·403·409·405·400·422) | **사유가 문장으로.** 접근 로그에는 없는 정보 |
| `ERROR` | `Unhandled exception returning INTERNAL_SERVER_ERROR` | **500만** | `_msg`는 일반 문구뿐. 실제 내용은 구조화된 `exception.*` |

**둘 다 `exception.*` 페이로드를 갖는다.** 500만 예외 객체를 남기는 것이 아니다 — 실행 `1788760757`에서 처리된 4xx 48건도 예외 필드를 갖고 있었다.

INFO 줄이 왜 중요한가. 접근 로그는 `403`과 경로까지만 알려준다. **무엇이 거부됐는지는 이 줄에만 있다.**

```
Principal 'nb_1788760757_denied' with activated PrincipalRoles '[nb_1788760757_denied_role]'
and activated grants via '[nb_1788760757_denied_role]' is not authorized for op LOAD_TABLE
```

`op LOAD_TABLE`, principal, 활성 role — 403 조사에 필요한 전부다. `Only Root principal(service-admin) can perform RESET_CREDENTIALS`, `The specified bucket does not exist (Status Code: 404, Request ID: …)`, `Failed to get subscoped credentials: UnknownHostException …`도 같다.

> ⚠ **이 로거의 레벨을 ERROR로 올리지 말 것.** 500은 ERROR 줄만으로 충분하지만(예외 객체를 갖고 있으므로), **4xx의 사유는 통째로 사라진다.** `polaris/values.yaml`이 `org.apache.polaris.service.catalog: DEBUG`를 "403 조사용"으로 켜 둔 목적과 정면으로 충돌한다. 용량 근거도 없다 — 4xx 하나당 한 줄, 실행 `1788760757` 기준 2,824 레코드 중 약 67줄(**2.4%**)이다.
>
> OpenSearch 화면에서는 `_msg`만 보이고 ERROR 줄의 `_msg`가 `Unhandled exception returning INTERNAL_SERVER_ERROR`뿐이라 INFO 줄이 유일한 정보처럼 보인다. 실제로는 500의 내용도 `exception.*`에 온전히 있다. **`_msg`만 보고 판단하지 말 것.**

### 6.3 플러시 리포트 — 개요

`dummy` INPUT이 5초마다 틱을 보내고, `WINDOW_SECONDS` 경계에서 필터가 그 틱을 **레코드 배열**로 치환하고 카운터를 리셋한다. Fluent Bit이 배열을 개별 레코드로 쪼갠다.

공통 봉투(envelope) — 3종 모두가 갖는다:

```
schema_version   report_type   report_seq   hostname
window_start     window_end    window_seconds   _time
```

> ⚠ **`_time`은 윈도의 *끝*이다.** `window_start 05:59:00`인 리포트는 `_time 05:59:30`에 나타난다. 3종이 같은 `_time`을 공유하므로 `stats by (_time)`으로 한 윈도를 묶을 수 있다.
> ⚠ **`report_seq`는 파드별 카운터이며 재시작하면 1로 돌아간다.** 두 세대에 걸쳐 `min`/`max`를 내면 존재하지 않는 공백이 만들어진다.

### 6.4 요약(summary)은 무엇을 수집해서 무엇을 쓰는가 ★

**수집 지점은 단 하나다.** `count_record()`가 규칙 3~7의 **어떤 판단보다 먼저** 호출된다. 그래서 "저장되지 않은 것"도 전부 집계에 들어간다. 이것이 이 설계의 전부다.

```
접근 로그 레코드 도착
   │
   ├─ access_seen +1                       ← 무조건
   ├─ min/max_record_time 갱신
   │
   ├─ 파싱 실패?  → parse_errors +1, 여기서 종료 (행에 잡히지 않음)
   │
   ├─ classify(path) 로 resource 키 결정
   ├─ resource 행과 principal 행 두 개를 동시에 증가
   │     requests +1
   │     GET|HEAD  → reads +1        POST|PUT|DELETE|PATCH → writes +1
   │     status>=400 → errors +1
   │          status>=500 → errors_5xx +1
   │          그 외      → errors_4xx +1,  401|403이면 auth_denied +1
   │     response_bytes += %b
   │
   └─ 그 다음에야 규칙 3~7이 저장 여부를 결정
```

**요약 필드 출처표** — 각 값이 무엇을 세고, 언제 증가하고, 무엇을 빼는지.

| 필드 | 세는 대상 | 증가 시점 | 주의 |
|---|---|---|---|
| `access_seen` | 접근 로그 레코드 **전부** | `count_record` 진입 즉시 | keep/count 판단 이전. 파싱 실패도 포함 |
| `parse_errors` | 파싱하지 못한 줄 | 파싱 실패 시 | 여기서 즉시 종료되므로 **resource/principal 행에는 잡히지 않는다** |
| `access_counted` | 개별 저장되지 **않은** 것 | 규칙 5(비관리 POST), 규칙 6(2xx GET/HEAD) | |
| `access_kept` | — | **`access_seen - access_counted` 뺄셈** | 독립 카운터가 아니다. 필터 내부에서는 **항등식**이므로 자기검증이 못 된다. 끝에서 끝까지 확인할 때만 *전송* 검사가 된다 |
| `counted_read` | 2xx GET/HEAD | 규칙 6 | v1의 `counted_get`은 HEAD도 세면서 이름이 GET이었다 |
| `counted_post` | `/api/management/` 밖의 POST | 규칙 5 | |
| `errors_kept` | 규칙 3으로 저장된 레코드 | 규칙 3 진입 시 | status>=400 **또는** 파싱 실패 **또는** status 없음 |
| `errors_4xx` | 400–499 | 행 단위 집계의 합 | **status가 nil이면 어느 쪽에도 넣지 않는다** — 파이프라인 자신의 실패를 "클라이언트 오류"가 흡수하지 않도록 |
| `errors_5xx` | 500 이상 | 행 단위 집계의 합 | |
| `auth_denied` | **401 또는 403** | 행 단위 집계의 합 | **`errors_4xx`의 부분집합이다.** 403은 두 필드를 모두 올린다 |
| `bytes_total` | `%b`의 총합 | resource 행들의 `response_bytes` 합 | principal 행은 더하지 않는다 — 이중 계상 방지 |
| `distinct_resources` | `requests > 0`인 resource 행 수 | 리포트 생성 시 | **캐리된 0행은 제외.** v1은 여기서 방출된 행 수를 세어, 트래픽 없는 윈도가 "리소스 2개를 접촉했다"고 보고했다 |
| `distinct_principals` | `requests > 0`인 principal 행 수 | 리포트 생성 시 | |
| `carried_rows` | `requests == 0`인 행 수 (resource + principal) | 리포트 생성 시 | |
| `resources_other` | `__other__`로 접힌 **요청 수** | `touch_resource` | 한 클라이언트가 URL 하나를 두드린 것과 스캐너가 20개를 훑은 것을 구별하지 못한다 |
| `resources_other_distinct` | 접힌 **서로 다른 키 수** | `touch_resource` | 위를 구별하기 위해 존재. 상한은 `REPORT_MAX_RESOURCES`(500) |
| `principals_other` | 상한 초과로 접힌 principal 요청 수 | `touch_principal` | 상한 200 |
| `windows_skipped` | 건너뛴 윈도 수 | `idx - 직전윈도 - 1` | **≥1이면서 min/max 간격이 `window_seconds`보다 넓다면 VM이 잠들었던 것** |
| `min_record_time` / `max_record_time` | 레코드 `_time`의 최소/최대 | `count_record` | RFC3339 고정 포맷이라 **문자열 비교로 충분**하다. 리플레이는 윈도가 며칠에 걸치는 것으로 드러난다 |
| `partial_window` | 첫 윈도인가 | 윈도 생성 시 | 문자열 `"true"`/`"false"` |

**빈 윈도에서는 `min_record_time`/`max_record_time`이 빈 문자열로 방출되고, VictoriaLogs는 빈 값을 저장하지 않는다.** 즉 필드가 아예 없다. 이 두 필드를 읽는 검사는 **부재를 0이나 "범위 안"으로 읽으면 안 된다.**

> ⚠ **`max_record_time`이 `window_end`보다 나중일 수 있다.** 레코드는 **도착한 윈도**에 집계되지, 자기 타임스탬프의 윈도에 집계되지 않는다. **[검증됨]** seq 196의 `max_record_time`은 `05:59:31.893`인데 `window_end`는 `05:59:30`이다. 경계 근처에서 "이 호출은 이 윈도에 있다"고 클라이언트 시각으로 가정하면 어긋난다.

**요약 레코드 예시** (실측, seq 196):

```json
{
  "report_type": "summary", "schema_version": "2", "report_seq": "196",
  "hostname": "fb-polaris-shipper-fluent-bit-55b7bf586d-5kt5l",
  "window_start": "2026-09-07T05:59:00Z", "window_end": "2026-09-07T05:59:30Z",
  "window_seconds": "30", "_time": "2026-09-07T05:59:30Z",
  "access_seen": "237", "access_kept": "107", "access_counted": "130",
  "counted_read": "107", "counted_post": "23",
  "errors_kept": "53", "errors_4xx": "46", "errors_5xx": "7", "auth_denied": "13",
  "parse_errors": "0", "bytes_total": "1963936",
  "distinct_resources": "35", "distinct_principals": "4", "carried_rows": "0",
  "resources_other": "36", "resources_other_distinct": "13", "principals_other": "0",
  "windows_skipped": "0", "partial_window": "false",
  "min_record_time": "2026-09-07T05:59:17.320247963Z",
  "max_record_time": "2026-09-07T05:59:31.893778096Z"
}
```

### 6.5 resource 행과 principal 행

```json
{
  "report_type": "resource", "report_seq": "196",
  "resource": "/api/catalog/v1/cat/namespaces/probe_ns/tables/probe_tbl",
  "resource_kind": "table",
  "requests": "47", "reads": "38", "writes": "9",
  "errors": "10", "errors_4xx": "10", "errors_5xx": "0", "auth_denied": "10",
  "response_bytes": "74593"
}
```

- **`response_bytes`는 합계다.** 최대값도 평균도 아니다. 평균은 `response_bytes / requests`로 구할 수 있지만 **최대값은 복원할 수 없다** — 개별 레코드가 없기 때문이다. (요약의 같은 집계는 `bytes_total`이라는 이름을 쓴다. 이름이 일관되지 않으니 주의.)
- 위 예시는 **요청 47건 중 10건이 전부 인증/인가 실패**라는 뜻이다. `auth_denied 10`은 `errors_4xx 10`에 **포함된** 값이다.

**`resource_kind`는 6종**이며 URL이 아니라 **리소스**로 키를 만든다.

| kind | 패턴 |
|---|---|
| `table` | `…/namespaces/{ns}/tables/{t}` |
| `view` | `…/namespaces/{ns}/views/{v}` |
| `collection` | `…/namespaces`, `…/namespaces/{ns}/tables`, `…/namespaces/{ns}/views` |
| `namespace` | `…/namespaces/{ns}` |
| `management` | `/api/management/` 하위 |
| `other` | 그 외 (`/config`, `/oauth/tokens`, `…/tables/rename` 등) |

`…/tables/{t}/metrics`는 **그 테이블 위로 접힌다.** v2는 테이블 하나에 행 두 개를 냈고, 그러면 그 테이블에 대한 모든 추세가 틀린다.

**에러는 리소스 키를 만들지 않는다.** 존재한 적 없는 테이블에 대한 404는 `__other__`로 간다. 클라이언트가 없는 이름을 두드려 키 공간을 채우지 못하게 하기 위해서다. **그 요청들의 카운트는 사라지지 않고 `__other__`에 들어가므로 마진 총합은 정확하게 유지된다.** 물론 그 요청 자체는 규칙 3으로 온전히 저장된다.

> 그래서 `resource` 필드가 가리키는 키와, 그 요청이 실제로 올린 행은 **다를 수 있다.**

### 6.6 마진과 겹침 — 무엇이 자기검증이고 무엇이 아닌가

**유일한 진짜 자기검증:**

```
sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors
```

두 개의 **독립적으로 구성된** 행 집합이 같은 총합을 내야 한다. 한쪽이 어긋나면 귀속이 틀린 것이다.

**[검증됨]** 트래픽이 있었던 윈도 **8개 중 8개**에서 정확히 성립했다.

> 단, **principal이 하나뿐이면 이 등식은 전역 카운터로도 만족된다.** 아무것도 귀속하지 않는 필터조차 통과한다. 의미를 가지려면 서로 다른 principal이 총합의 일부씩을 나눠 가져야 한다.

**겹침 규칙 — 절대 더하지 말 것:**

- `reads`/`writes`는 **메서드**로, `errors`는 **상태 코드**로 센다. 실패한 GET은 양쪽에 들어간다. → `reads + writes + errors`는 의미 없는 수다.
- `auth_denied ⊂ errors_4xx ⊂ errors`. → `errors_4xx + errors_5xx + auth_denied`는 중복 계상이다.
- 성립하는 것: `reads + writes <= requests`, `errors <= requests`, `errors_4xx + errors_5xx <= errors` (status가 nil인 경우 때문에 **등호가 아닐 수 있다**).

**`access_kept + access_counted == access_seen`은 자기검증이 아니다.** 필터가 `access_kept`를 뺄셈으로 만들기 때문에 항등식이다. 끝에서 끝까지 확인할 때만 **Fluent Bit의 배열 분할과 VictoriaLogs의 ingest를 검사하는 전송 검사**가 된다.

### 6.7 캐리와 감쇠

트래픽이 있던 행은 **다음 윈도에 명시적 0으로 한 번 더 방출된다.** 0에 머문 행은 다시 캐리되지 않으므로 집합이 **감쇠**한다.

```
윈도 N   : 리소스 35개 활성
윈도 N+1 : 그중 트래픽 없는 것들이 0으로 캐리 → carried_rows 에 계상
윈도 N+2 : 계속 0이면 사라짐
```

**[검증됨]** 두 단계 모두 실측으로 확인했고, 완전히 유휴한 윈도는 **행이 0개**다(요약 하나만 방출). 캐리가 누적되지 않는다.

값이 0인 행은 **"측정했더니 0"** 이라는 뜻이지 "데이터 없음"이 아니다. 대시보드에서 이 둘을 구별할 수 있게 해준다.

### 6.8 v1 → v2, 그리고 두 스키마가 섞여 있다는 것 ⚠

v2가 바꾼 것:

| 변경 | 이유 |
|---|---|
| `counted_get` → **`counted_read`** | `READ_METHODS`가 GET **과** HEAD인데 이름이 GET이라 정의상 과소계상 |
| `errors_4xx` / `errors_5xx` / `auth_denied` 추가 | v1은 404와 500을 같은 정수에 담아 구별할 수 없었다 |
| `bytes_total`, `response_bytes` 추가 | |
| `distinct_resources` / `_principals` 와 `carried_rows` 분리 | v1은 *방출된* 행 수를 *접촉한* 리소스라는 이름으로 보고했다 |
| `resources_other_distinct`, `windows_skipped` 추가 | |

> ⚠ **리포트 스트림에는 v1 레코드와 v2 레코드가 함께 들어 있다.** shipper 파드가 `2026-09-07T04:21:30Z`에 교체되었고, 그 이전 레코드는 `schema_version: 1`이다.
>
> 그 시점을 걸치는 범위에서 `sum(errors_4xx)`를 내면 **조용히 과소계상된다** — v1 레코드에는 그 필드가 없고, 합계에서 부재는 0처럼 행동하기 때문이다.
>
> **모든 리포트 스트림 질의에 `schema_version:2`를 붙일 것.** 시퀀스 연속성을 볼 때는 `hostname`도 함께.

---

## 7. LogsQL 쿼리 모음

### 7.1 기본형

**VM-UI**(`$V/select/vmui`)는 탐색에는 좋지만 **결론을 내리는 데 쓰지 말 것** — 7.4를 먼저 읽는다. 재현 가능한 결과는 `curl`로 낸다.

```bash
V=http://192.168.139.2:9428
q() { curl -s "$V/select/logsql/query" \
  --data-urlencode "query=$1" \
  --data-urlencode "start=${2:-2026-09-07T00:00:00Z}" \
  --data-urlencode "end=${3:-2026-09-08T00:00:00Z}" \
  --data-urlencode 'limit=0'; }

q 'app:polaris http_status:>=500' | jq -c .
```

**시간 범위는 쿼리 문자열이 아니라 요청 파라미터(`start`/`end`)에 넣는다.**

### 7.2 조사 시나리오

**모든 예제에 `level`을 포함시켰다.** 같은 로거가 INFO와 ERROR를 모두 내보내므로(§6.2), 레벨이 보이지 않으면 결과를 잘못 읽는다.

```bash
# 특정 요청이 남긴 모든 줄 (접근 로그 + 애플리케이션 로그)
q 'app:polaris mdc.requestId:"nb-1788760757-006-iceberg-create_namespace"
   | fields _time, level, loggerName, http_status, _msg'

# 어떤 principal이 무엇을 했는가 — 저장된 것만
q 'app:polaris user_principal_name:"nb_1788760757_denied"
   | fields _time, level, http_method, api_path, http_status'

# 인가 실패 전부
q 'app:polaris http_status:403 OR http_status:401
   | stats by (level, user_principal_name, api_path) count() as n'

# 403이 "왜" 거부됐는가 — 접근 로그에는 없는 정보. INFO 줄에만 있다
q 'app:polaris level:INFO
   loggerName:"org.apache.polaris.service.exception.IcebergExceptionMapper"
   _msg:"not authorized for op"
   | fields _time, level, _msg, mdc.requestId'

# 500만 보기 — 이 로거의 ERROR 줄이 곧 500이다
q 'app:polaris level:ERROR
   loggerName:"org.apache.polaris.service.exception.IcebergExceptionMapper"
   | fields _time, level, exception.exceptionType, exception.message, mdc.requestId'

# 500의 접근 로그 쪽 절반 — 어떤 엔드포인트였는가
q 'app:polaris http_status:500
   | fields _time, level, http_method, api_path, user_principal_name'

# 한 로거의 두 층위를 나란히 — INFO 사유와 ERROR 500이 어떻게 짝을 이루는지
q 'app:polaris loggerName:"org.apache.polaris.service.exception.IcebergExceptionMapper"
   | fields _time, level, _msg, exception.exceptionType, mdc.requestId'

# 자격증명 리셋 — v2에서는 흔적이 남지 않던 바로 그 호출
q 'app:polaris api_path:"/reset" http_method:POST
   | fields _time, level, user_principal_name, http_status'

# 파서가 깨졌는지 — 정기 점검 항목
q 'app:polaris access_log_parse_error:true | stats by (level) count() as n'

# 저장 용량을 무엇이 차지하는가 — 레벨별로 나누면 어디가 시끄러운지 바로 보인다
q 'app:polaris | stats by (loggerName, level) count() as n | sort by (n) desc'
```

> 접근 로그 레코드는 `io.quarkus.http.access-log`가 INFO로 남기므로 **`level`이 항상 `INFO`다.** 애플리케이션 레코드에서만 레벨이 실제로 갈린다.

### 7.3 리포트 스트림 집계

리포트 스트림의 레코드는 **`level`이 항상 `REPORT`다** — 그것이 스트림 선택자이기 때문이다. 심각도로 읽을 값이 아니며, 구분자는 `report_type`이다.

```bash
R='app:polaris-shipper-report schema_version:2'

# 어떤 리소스가 뜨거운가
q "$R report_type:resource | stats by (resource) sum(requests) as req | sort by (req) desc"

# 누가 부하를 만드는가
q "$R report_type:principal | stats by (user_principal_name) sum(requests) as req"

# 성공한 읽기의 총량 — 개별 레코드로는 존재하지 않는 것
q "$R report_type:summary | stats sum(counted_read) as reads, sum(access_kept) as kept"

# 시간대별 에러
q "$R report_type:summary | stats by (_time) sum(errors_4xx) as c4, sum(errors_5xx) as c5"

# 5xx가 난 윈도만
q "$R report_type:summary errors_5xx:>0 | stats by (_time) sum(errors_5xx) as fivexx"
```

### 7.4 함정 여섯 가지 ⚠ — 전부 실제로 잘못된 결론을 만들었다

1. **VM-UI는 쿼리 안의 시간 범위를 무시하고, 결과를 몇 행으로 자른다.** 이것이 보이지 않는다. `04:21~04:26`을 요청했는데 `05:58~06:00`의 5행이 돌아왔다. **결론은 `curl`로 낼 것.**
2. **모든 카운트에는 분모를 붙인다.** 먼저 `stats count()`로 범위를 확인한다. 범위가 빠진 숫자는 답처럼 보인다 — `POST …/namespaces`의 500이 **25건**으로 나왔지만 범위를 맞추니 **6건**이었다.
3. **`report_seq`는 파드별이다.** 두 세대에 걸쳐 `min`/`max`를 내면 존재하지 않는 25분짜리 공백이 만들어진다. `hostname`을 반드시 함께 건다.
4. **리포트 스트림에 v1과 v2가 섞여 있다.** `schema_version:2`를 붙이지 않으면 v2 필드의 합계가 조용히 줄어든다.
5. **`sum()`은 빈 그룹에서 `NaN`을 낸다. `count()`는 0을 낸다.** v1 요약에는 `carried_rows`가 없어 합이 NaN이 되고, 이를 불일치로 오독하기 쉽다.
6. **`_time`은 윈도의 끝이다.** 그리고 레코드는 **도착한** 윈도에 집계된다. 클라이언트 시각으로 윈도를 가정하면 경계 근처에서 어긋난다.

> 공통 교훈 하나: **부재는 0이 아니다.** 없는 필드를 0으로 읽으면 아무도 하지 않은 측정에 대해 PASS가 보고된다. `0 of 0`은 답이 아니다.

---

## 8. 운영

### 8.1 건강 상태 체크리스트

아래는 **[검증됨]** — 2026-09-07에 실제로 돌린 결과다. 정기 점검으로 그대로 쓸 수 있다.

| 검사 | 쿼리 | 기대 | 실측 |
|---|---|---|---|
| 리포트 연속성 | `report_seq`의 `min`/`max`/`count` (한 host, `schema_version:2`) | `hi - lo + 1 == n` | **1 / 417 / 417 — 공백도 중복도 없음** |
| 마진 등식 | 6.6 참조 | 트래픽 있는 모든 윈도에서 성립 | **8 / 8 정확** |
| 캐리 계상 | `requests:0`인 행 수 == `carried_rows` | 모든 윈도 | **406 / 406** |
| 시작 사각지대 | `report_seq:1` | `partial_window: true` | **[검증됨] 그렇고, `access_seen 0`** |
| 파서 건강 | `access_log_parse_error:true` | 0 | 0 |
| 전송 손실 | `fluentbit_output_{errors,retries,dropped}_total` | 0 | 0 |

```bash
# 연속성 — 가장 강한 진술
q 'app:polaris-shipper-report report_type:summary schema_version:2
   hostname:"<현재 파드명>" | stats min(report_seq) as lo, max(report_seq) as hi, count() as n'

# Fluent Bit 메트릭
kubectl -n datahub-hynix port-forward deploy/fb-polaris-shipper 2020:2020 &
curl -s localhost:2020/api/v1/metrics/prometheus | grep -E 'output_(errors|retries|dropped)'
```

### 8.2 알려진 이슈

**용량 — 보존 정책이 다루는 것은 전체의 2.4%다.**
**[검증됨]** 실행 `1788760757`: 157 호출에 **2,824 레코드**(호출당 18개). 그중 접근 로그는 **68건(2.4%)**, 나머지 2,756건은 규칙 2로 그대로 통과한 애플리케이션 로그다. 로거별로는 `DatasourceOperations` 하나가 **1,679건(59%)**.

> 보존 정책은 **감사 충실도** 제어 장치이지 저장 용량 제어 장치가 아니다. 용량을 줄이려고 규칙 3~7을 손보는 것은 잘못된 2.4%를 손보는 것이다. 용량의 지렛대는 DEBUG SQL 레코드이고, 방향은 이미 정해져 있다 — **레벨을 낮추지 말고 경로를 분리할 것**(§3.4).

**Polaris가 생성 경로에서 500을 낸다 (`active-issues.md` #15).**
**[검증됨]** 모든 500은 `IcebergExceptionMapper`를 거친 `NullPointerException`이다. 6건이 `POST …/{catalog}/namespaces`이고, **그중 3건은 새로 만든 카탈로그 3개 각각의 첫 네임스페이스 생성**이다. 카탈로그를 만들고 곧바로 그 안에 네임스페이스를 만들면 500이 난다. 네임스페이스 자체는 그 뒤로 정상 사용된다 — 커밋은 되었고 그 후 resolve가 null을 참조한 것으로 보인다.

**[검증됨]** 약 400개 윈도 중 **5개 윈도, 총 15건**이며 전부 실행 시점에 몰려 있다. 유휴 시간대는 깨끗하다. 즉 배경에서 나는 고장이 아니라 **생성 경로 고장**이다.

**시작 사각지대.** `report_tick`은 첫 틱에서 첫 윈도를 연다. shipper 시작과 첫 틱 사이에 처리된 레코드는 정책대로 라우팅되지만 **어느 리포트에도 나타나지 않는다.** 틱 간격(현재 5초)으로 상한이 잡히고, 해당 윈도는 `partial_window: true`로 표시된다. **[검증됨]** 이 파드에서는 그 구간의 트래픽이 0이어서 손실이 없었다.

**성공한 네임스페이스 생성은 개별 레코드를 남기지 않는다.** `/api/catalog/…/namespaces`는 `/api/management/` 하위가 아니라 규칙 5의 counted-only에 걸린다. 따라서 `stats by (http_status)`로 이 경로를 조회하면 **어떤 범위에서도 에러만 나온다.** 성공 건수는 리포트의 `writes` 안에만 있다.

### 8.3 구조적으로 기록되지 않는 것 — 정책과 무관하다

1. **`%D`가 없다.** 어떤 요청의 소요시간도 어디에도 기록되지 않는다. 클라이언트 측 측정이 유일한 출처다.
2. **접근 로그는 응답이 쓰일 때 기록된다.** 따라서 **행(hang) 상태로 끝나지 않는 요청은 줄 자체가 남지 않는다.** 이 파이프라인은 그것을 보지 못한다.
3. **`grant_privilege` PUT이 *무엇을* 허용했는지는 애플리케이션 로그 한 줄에만 남는다.** PUT 자체는 저장되지만 그 내용의 감사 가능성은 **보존 정책이 아니라 Polaris 로거 레벨에 달려 있다.** v3는 "누가 principal을 만들었는가"를 닫았고, "어떤 권한이 부여되었는가"는 아직 열려 있다.
4. **"누가 인증했는가"는 의도적으로 답할 수 없다.** `POST /oauth/tokens`는 규칙 5의 counted-only다. 실패한 인증(401)은 규칙 3으로 남으므로, **"누가 실패했는가"만 답할 수 있다.**

### 8.4 실행(run)을 무효화하는 것

커버리지 실행 전후로 반드시 기록한다.

- **Polaris 스케일링.** HPA가 3 레플리카를 허용하고, 셋이 같은 로그 파일에 append한다 (#8).
- **shipper 재시작.** `report_seq`가 1로 돌아가고, emptyDir이 새로 생기면 `Read_from_Head`가 파일 전체를 재전송한다.
- **리포트 스트림의 공백은 대개 OrbStack VM이 노트북과 함께 잠든 것**이지 필터가 멈춘 것이 아니다. **잠을 걸치는 리포트 스트림 측정은 경과 시간으로 읽으면 안 된다.**

---

## 9. 부록

### 9.1 파일 맵

| 경로 | 내용 |
|---|---|
| `logging/fb-values.yaml` | shipper values + **Lua 정책·리포트 정본** |
| `logging/victoria-values.yaml` | VictoriaLogs values |
| `logging/scripts/test-polaris-filters.py` | 배포된 Lua를 추출해 실행하는 테스트 (60/60) |
| `2026-09-03-2026-09-03-polaris-logging-architecture-spec.md` | 설계 문서(의도). §7에 LogsQL 레시피 |
| `2026-09-07-HANDOFF-report-schema-v2.md` | 리포트 스키마 v2의 근거와 결정 |
| `2026-09-07-PLAN-log-coverage-schema-v2.md` | 하네스가 갚아야 할 항목 |
| `polaris/values.yaml` | Polaris 차트 values (로깅 블록 포함) |
| `shipper-v3-upgrade-runbook.md` | 업그레이드/복귀 절차 |
| `.memory/active-issues.md` | **값이나 런북을 믿기 전에 볼 것** |
| `.memory/roadmap.md` | 다음 할 일과 숫자가 붙은 사실 |
| `MEMORY.md` | 색인. 무엇이 다음이고 무엇이 적혀만 있는지 |

`polaris-learning/log-coverage/`는 이 파이프라인을 검증하는 별도 저장소다. **배포된 Lua를 오라클로 실행**하므로 테스트가 배포된 것과 어긋날 수 없다.

### 9.2 용어

| 용어 | 뜻 |
|---|---|
| **kept** | 개별 레코드로 VictoriaLogs에 저장됨 |
| **counted** | 저장되지 않고 윈도 집계에만 반영됨 |
| **carry / 캐리** | 트래픽이 있던 행을 다음 윈도에 명시적 0으로 한 번 더 방출 |
| **decay / 감쇠** | 0에 머문 행이 그 다음 윈도에서 사라짐 |
| **margin / 마진** | resource 합 == principal 합 == `access_seen - parse_errors` |
| **oracle / 오라클** | 배포된 Lua를 그대로 실행해 "기대값"을 만드는 방식 |
| **`__other__`** | 상한을 넘었거나 키를 만들 수 없는 요청이 접히는 행 |

### 9.3 이 문서가 "완료"라고 말하는 범위

README의 질문 — *내일 이 엔드포인트에서 문제가 생기면 기록이 남는가* — 에 대해, **접근 로그 표면에 대해서는 "그렇다"** 이며 §8.3의 네 가지 예외를 갖는다. 그 판단의 근거는 417개 연속 윈도에 대한 실측이다.

아직 닫히지 않은 것:

1. **임시 설정 복귀** — `WINDOW_SECONDS` 1800, `Interval_Sec` 30, `resources_other`의 `_msg` 수정 동반. **선택이 아니라 의무다.**
2. **DEBUG SQL 레코드 경로 분리** — 전체 용량의 대부분. 방향은 정해졌고 착수하지 않았다.
3. **리포트 스트림에 대한 알림** — 이 클러스터에 VictoriaMetrics가 없다.
4. **tail 상태 PVC** — `helm upgrade`가 로그 전체를 중복시킬 수 있다.

---

*이 문서의 수치는 2026-09-07 실행 `1788760757` 및 같은 날 리포트 스트림 실측에서 왔다. 값이 바뀌면 문서도 같은 커밋에서 바꾼다 — 아무도 갱신하지 않은 리포트는 리포트가 없는 것보다 나쁘다.*
