#!/usr/bin/env python3
"""Generate the Korean sample-data guide from two OpenSearch exports.

    python3 logging/scripts/step14-sample-doc.py DETAIL.json REPORT.json > logging/GUIDE-sample-data-YYYY-MM-DD.ko.md

DETAIL.json  a search response over polaris-logs-*   (the detail index)
REPORT.json  a search response over polaris-report-* (the window reports)

Both may be raw copies of the Dev Tools response panel: triple-quoted multi-line
strings are converted here, exactly as logging/scripts/devtools-json-fix.py does it.
Dev Tools re-indents the inside of those strings, so a `message` with newlines can
differ from the index in whitespace -- for byte-exact samples export with curl.

WHY THIS EXISTS. The 2026-09-16 edition of this guide was written by hand, and when
threadName/threadId came back on 2026-09-18 (#42) every one of its ~100 samples was
silently wrong: they showed a document shape no index had carried since 09-19, and
the guide's own header said those fields no longer existed. A sample document must
be a copy of a real one, so the guide is generated from an export and never retyped.

The numbers in section 1 are computed from the two files, not restated from a plan.
Nothing here validates the data: use step10/step11 for that. If the export is from a
run whose invariants failed, this will faithfully document a broken window.

The output is deterministic: samples are chosen by explicit rules and ties broken by
(@timestamp, _id), so regenerating from the same export gives the same document.
"""
import json, re, sys, collections

# ── input ────────────────────────────────────────────────────────────────────────────

def load(path):
    raw = open(path, encoding="utf-8").read()
    fixed = re.sub(r'"""(.*?)"""', lambda m: json.dumps(m.group(1), ensure_ascii=False), raw, flags=re.S)
    doc = json.loads(fixed)
    hits = doc.get("hits", {}).get("hits", doc if isinstance(doc, list) else [])
    return [{"_id": h.get("_id"), "_index": h.get("_index"), **h["_source"]} for h in hits]

# ── rendering ────────────────────────────────────────────────────────────────────────

DETAIL_ORDER = ["@timestamp", "_time", "level", "loggerName", "message", "threadName", "threadId",
                "user_principal_name", "client_ip", "http_method", "api_path", "http_status",
                "response_size", "exception", "hostName", "mdc", "sequence",
                "access_log_parse_error", "secret_redacted"]
REPORT_ORDER = ["@timestamp", "_time", "schema_version", "report_type", "report_seq", "hostname",
                "window_start", "window_end", "window_seconds", "partial_window", "message",
                "resource", "resource_kind", "api_kind", "user_principal_name", "logger_name",
                "dropped", "requests", "reads", "writes", "errors", "errors_4xx", "errors_5xx",
                "auth_denied", "response_bytes", "last_read_bytes", "last_write_bytes",
                "commit_count", "commit_ms_sum", "commit_ms_min", "commit_ms_max"]

def clean(src):
    """Drop bookkeeping keys and anything with no value -- as stored, minus the empties."""
    out = {}
    for k, v in src.items():
        if k in ("_id", "_index"):        continue
        if v is None or v == "" or v == {} or v == []: continue
        out[k] = v
    return out

FRAME_KEYS = {"class", "method", "line", "file"}

def compact_frames(txt):
    """Put each stack frame object on one line. A 103-frame trace is 500+ lines at indent 2
    and unreadable; one line per frame is how a stack trace is meant to be read anyway."""
    def one(m):
        inner = " ".join(x.strip() for x in m.group(1).strip().split("\n"))
        return "{" + inner + "}"
    pat = re.compile(r"\{\n((?:\s*\"(?:class|method|line|file)\": [^\n]*\n)+)\s*\}")
    prev = None
    while prev != txt:
        prev, txt = txt, pat.sub(one, txt)
    return txt

def block(src, order):
    d = clean(src)
    keys = [k for k in order if k in d] + sorted(k for k in d if k not in order)
    txt = json.dumps({k: d[k] for k in keys}, ensure_ascii=False, indent=2)
    return "```json\n" + compact_frames(txt) + "\n```"

def sort_key(d):
    return (d.get("@timestamp", ""), d.get("_id") or "")

# ── analysis ─────────────────────────────────────────────────────────────────────────

ACCESS_LOGGER = "io.quarkus.http.access-log"

class Data:
    def __init__(self, detail, report):
        self.detail  = sorted(detail, key=sort_key)
        self.report  = sorted(report, key=sort_key)
        self.access  = [d for d in self.detail if d.get("loggerName") == ACCESS_LOGGER]
        self.app     = [d for d in self.detail if d.get("loggerName") != ACCESS_LOGGER]
        self.summary = [r for r in self.report if r.get("report_type") == "summary"]
        self.res     = [r for r in self.report if r.get("report_type") == "resource"]
        self.pri     = [r for r in self.report if r.get("report_type") == "principal"]
        self.drop    = [r for r in self.report if r.get("report_type") == "app_dropped"]
        self.detail_index = self.detail[0]["_index"] if self.detail else "?"
        self.report_index = self.report[0]["_index"] if self.report else "?"
        self.date = self.detail_index.split("-")[-1].replace(".", "-") if self.detail else "?"
        self.fb_pods = sorted({r.get("hostname") for r in self.report if r.get("hostname")})
        self.pl_pods = sorted({d.get("hostName") for d in self.detail if d.get("hostName")})
        self.windows = sorted({r.get("window_start") for r in self.summary})
        self.busy    = sorted(self.summary, key=lambda r: -r.get("access_seen", 0))
        self.loggers = collections.Counter(d.get("loggerName") for d in self.app)

    def tot(self, field):
        return sum(r.get(field, 0) for r in self.summary)

    def rows_of(self, window):
        return [r for r in self.res if r.get("window_start") == window]

def pick(cands, **eq):
    """First document matching all equalities, in (@timestamp, _id) order."""
    for d in cands:
        if all(d.get(k) == v for k, v in eq.items()):
            return d
    return None

STATUS_LABEL = {200: "200 OK", 201: "201 Created", 202: "202 Accepted", 204: "204 No Content",
                400: "400 Bad Request", 401: "401 Unauthorized", 403: "403 Forbidden",
                404: "404 Not Found", 409: "409 Conflict", 500: "500 Internal Server Error"}

def sig(msg):
    """A message's shape, ignoring the identifiers in it -- so 'Adding grant X to Y' and
    'Adding grant P to Q' count as one sample, but a different sentence does not."""
    m = re.sub(r"[0-9]+", "#", (msg or "").splitlines()[0] if msg else "")
    m = re.sub(r"[A-Za-z_][A-Za-z0-9_.]*(?:_\d+|\d{4,})[A-Za-z0-9_.]*", "ID", m)
    return m[:60]

def kind_of(path):
    if "/api/management/" in path: return "management API"
    if "/api/catalog/"   in path: return "catalog API"
    return "API"

# ── document ─────────────────────────────────────────────────────────────────────────

def emit(d, argv):
    P = []
    w = P.append
    date = d.date
    n_acc, n_app = len(d.access), len(d.app)
    seen, kept, counted = d.tot("access_seen"), d.tot("access_kept"), d.tot("access_counted")
    c404, cread, cpost = d.tot("counted_404"), d.tot("counted_read"), d.tot("counted_post")
    dropped, dropped404 = d.tot("app_dropped_total"), d.tot("app_dropped_404")
    e4, e5, den = d.tot("errors_4xx"), d.tot("errors_5xx"), d.tot("auth_denied")
    statuses = collections.Counter(a.get("http_status") for a in d.access)
    zero = [r for r in d.summary if r.get("access_seen", 0) == 0]
    # The operational window is a decision that moves (30 s verification -> 1800 -> 3600 on 2026-09-21,
    # with 2 h still a candidate). Describe what the export carries rather than restating a target that
    # will age -- the guide is regenerated, the sentence should not need editing when the value changes.
    ws = d.summary[0].get("window_seconds") if d.summary else None
    wnote = (", 검증용 길이; 운영 목표는 3600초 = 1시간 (2026-09-21 결정, 모니터링 중 재조정 가능)"
             if ws is not None and ws < 600 else
             f" = {ws // 60}분" if ws else "")

    w(f"""# OpenSearch 샘플 데이터 — `polaris-logs-*` (상세) · `polaris-report-*` (요약), 스키마 v6 — {date}

> 신규 엔지니어 공유용 샘플입니다. **이 문서는 손으로 쓴 것이 아니라 실제 export 에서 생성됩니다.**
> 다시 만들려면:
>
> ```bash
> python3 logging/scripts/step14-sample-doc.py <상세.json> <요약.json> > logging/GUIDE-sample-data-{date}.ko.md
> ```
>
> - 원본: `{d.detail_index}` {len(d.detail)}건 · `{d.report_index}` {len(d.report)}건 (Dev Tools export).
> - **값이 없는 필드는 싣지 않았습니다** (문서에 없는 필드, 빈 문자열, 빈 객체). 보이는 필드가 그 문서에 실제로 저장된 전부입니다.
> - 값은 저장된 타입 그대로입니다 — 숫자는 숫자(`403`, `184`), 불리언은 불리언. (Dashboards CSV export 와 달리 쉼표 포맷·문자열 변환이 없습니다.)
> - `message` 의 줄바꿈은 JSON 규칙에 따라 `\\n` 으로 이스케이프했습니다. Dev Tools 응답 패널을 거쳤기 때문에 **여러 줄 `message` 의 들여쓰기 공백은 원본과 다를 수 있습니다** (값의 내용은 같음).
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

- **상세 `{d.detail_index}`** ({len(d.detail)}건): Polaris 파드 `{', '.join(d.pl_pods)}` 의 로그 중 **적재 대상만** 남은 문서.
  {d.detail[0]['@timestamp']} ~ {d.detail[-1]['@timestamp']}""")

    for lg, n in [(ACCESS_LOGGER, n_acc)] + d.loggers.most_common():
        lv = collections.Counter(x.get("level") for x in d.detail if x.get("loggerName") == lg)
        lvs = " / ".join(f"{k} {v}" for k, v in sorted(lv.items()))
        w(f"  - `{lg}` {n}건 ({lvs})")

    w(f"""- **요약 `{d.report_index}`** ({len(d.report)}건): Fluent Bit 파드 `{', '.join(d.fb_pods)}` 가 윈도우
  `{d.windows[0]}` ~ `{d.summary[-1].get('window_end')}` ({d.summary[0].get('window_seconds')}초{wnote}) 를 닫으며 만든 행. 윈도우 {len(d.windows)}개.
  - `report_type`: `summary` {len(d.summary)} / `principal` {len(d.pri)} / `resource` {len(d.res)} / `app_dropped` {len(d.drop)}
- **트래픽은 윈도우 {len([r for r in d.summary if r.get('access_seen',0)>0])}개에만 있습니다.** 나머지 {len(zero)}개는 `access_seen: 0` 인 빈 summary 행입니다 — 30초 윈도우를 쓰는 동안은 이렇게 빈 행이 대부분을 차지합니다.
- **적재되지 않은 것은 요약에 숫자로 남습니다.** 이 구간의 access log 는 **{seen}줄**이었고 그중 **{kept}줄**만 상세 인덱스에 있습니다.
  나머지 {counted}줄(성공한 조회 {cread}, catalog POST {cpost}, **404 {c404}**)은 `summary`·`resource`·`principal` 행의 카운터로만 존재합니다.
  허용 목록 밖 애플리케이션 로그 {dropped}줄은 `app_dropped` 행에, 404 요청에 딸린 앱 로그 {dropped404}줄은 `summary.app_dropped_404` 에 있습니다.
- 상세 인덱스의 access 문서 {n_acc}건은 `access_kept` {kept} 과 일치하고, 앱 로그 {n_app}건이 더해져 {len(d.detail)}건입니다.
- 오류 분포: {', '.join(f'`{k}` {v}건' for k, v in sorted(statuses.items()) if k)} — `errors_4xx` {e4}, `errors_5xx` {e5}, `auth_denied` {den} (404 집계분 포함).
- 권한 매트릭스 테스트가 일부러 에러를 유발한 실행이라 에러 비율이 운영보다 훨씬 높습니다.
- 같은 요청의 로그는 `mdc.requestId` 로, 같은 집계 윈도우의 요약 행은 `window_start` + `hostname` (또는 `report_seq` + `hostname`) 으로 묶입니다.

---

## 2. 상세 — HTTP Access Log

`message` 는 Quarkus 액세스 로그 원문이고, 파이프라인이 그것을 `client_ip` · `user_principal_name` · `http_method` · `api_path` · `http_status` · `response_size` 로 분해합니다. `user_principal_name: "-"` 는 결측이 아니라 **미인증/인증 실패**입니다.

**404 는 여기에 없습니다** — 정책 v5 는 404 를 세기만 하고 문서로 남기지 않습니다 (이 구간 {c404}건).
""")

    i = 0
    for st in sorted(statuses):
        if st is None: continue
        doc = pick(d.access, http_status=st)
        if not doc: continue
        i += 1
        w(f"#### 2.{i} {STATUS_LABEL.get(st, st)} — {doc.get('http_method')} ({kind_of(doc.get('api_path',''))})\n")
        w(block(doc, DETAIL_ORDER) + "\n")

    w("""---

## 3. 상세 — Admin 감사 로그 (PolarisServiceImpl)

관리 API 가 "무엇을 바꿨는지" 를 남기는 로그입니다. 액세스 로그가 *요청*을 기록한다면 이쪽은 *결과*를 기록합니다 — 둘은 `mdc.requestId` 로 조인합니다.
""")
    seen_shapes, j = set(), 0
    for doc in [x for x in d.app if "PolarisServiceImpl" in (x.get("loggerName") or "")]:
        shape = sig(doc.get("message"))
        if shape in seen_shapes: continue
        seen_shapes.add(shape); j += 1
        if j > 4: break
        w(f"#### 3.{j} {(doc.get('message') or '').splitlines()[0][:70]}\n")
        w(block(doc, DETAIL_ORDER) + "\n")

    w("""---

## 4. 상세 — Exception Mapper (INFO)

`IcebergExceptionMapper` 는 예외를 HTTP 응답으로 바꾸면서 **왜 실패했는지**를 남깁니다. `INFO` 는 "정상적으로 거부한" 경우입니다 — 권한 없음, 이미 있음, 잘못된 입력. 같은 요청의 액세스 로그(4xx)와 짝입니다.
""")
    k = 0
    seen_shapes = set()
    for doc in [x for x in d.app if "IcebergExceptionMapper" in (x.get("loggerName") or "") and x.get("level") == "INFO"]:
        shape = sig(doc.get("message"))
        if shape in seen_shapes: continue
        seen_shapes.add(shape); k += 1
        if k > 3: break
        w(f"#### 4.{k} {(doc.get('message') or '').splitlines()[0][:70]}\n")
        w(block(doc, DETAIL_ORDER) + "\n")

    errs = [x for x in d.detail if x.get("level") in ("ERROR", "WARN")]
    w(f"""---

## 5. 상세 — ERROR + Stack Trace

**규칙 1: `ERROR` 와 `WARN` 은 허용 목록과 무관하게 무조건 적재됩니다.** 그래서 이 절의 문서에는 `APP_ALLOW` 에 없는 logger 도 나옵니다 — 새 logger 가 조용히 사라지지 않게 하려는 설계입니다.

이 구간의 ERROR/WARN 은 {len(errs)}건입니다.
""")
    m, seen_shapes = 0, set()
    for doc in errs:
        ex = doc.get("exception") or {}
        shape = (doc.get("loggerName"), ex.get("exceptionType"), (ex.get("message") or "")[:40])
        if shape in seen_shapes: continue
        seen_shapes.add(shape); m += 1
        if m > 4: break
        label = f"`{(doc.get('loggerName') or '').split('.')[-1]}` — {ex.get('exceptionType', 'no exception field')}"
        w(f"#### 5.{m} {label}\n")
        w(block(doc, DETAIL_ORDER) + "\n")

    # section 6 -- requestId with the most documents
    groups = collections.defaultdict(list)
    for doc in d.detail:
        rid = (doc.get("mdc") or {}).get("requestId")
        if rid: groups[rid].append(doc)
    best = max(groups.items(), key=lambda kv: (len(kv[1]), kv[0])) if groups else (None, [])
    w(f"""---

## 6. 상세 — requestId 단위 요청 추적

`mdc.requestId` 는 한 요청이 남긴 모든 줄을 묶습니다. 액세스 로그(무엇을 요청했나) + 예외 로그(왜 실패했나) + 관리 로그(무엇이 바뀌었나).

**파이프라인이 이것을 판정에도 씁니다**: 허용 목록 앱 로그는 같은 `requestId` 의 액세스 라인이 올 때까지 보류되고, 그 요청이 404 면 **함께 버려집니다** (`app_dropped_404`). 그래서 상세 인덱스에 남은 앱 로그는 "적재된 요청의 앱 로그" 뿐입니다.

아래는 이 구간에서 가장 많은 줄을 남긴 요청 `{best[0]}` ({len(best[1])}건) 입니다.
""")
    shown = sorted(best[1], key=sort_key)[:6]
    if len(best[1]) > len(shown):
        w(f"*({len(best[1])}건 중 처음 {len(shown)}건)*\n")
    for n_, doc in enumerate(shown, 1):
        w(f"#### 6.{n_} `{(doc.get('loggerName') or '').split('.')[-1]}`\n")
        w(block(doc, DETAIL_ORDER) + "\n")

    busy = d.busy[0]
    w(f"""---

## 7. 요약 — summary

윈도우당 **한 행**. 그 윈도우에서 무슨 일이 있었는지의 전체 수치이고, **적재되지 않은 요청의 유일한 기록**입니다.

`message` 는 사람이 읽는 한 문장이며 v6 에서는 `summary` 행에만 있습니다. `partial_window` 는 **불리언이 아니라 문자열** `"true"`/`"false"` 입니다.

#### 7.1 트래픽이 있던 윈도우 (`{busy.get('window_start')}`)
""")
    w(block(busy, REPORT_ORDER) + "\n")
    if zero:
        w(f"#### 7.2 빈 윈도우 — 이 export 의 {len(zero)}/{len(d.summary)} 개가 이 모양입니다\n")
        w(block(zero[0], REPORT_ORDER) + "\n")

    w("""---

## 8. 요약 — principal

`user_principal_name` 별 한 행. **누가** 얼마나 요청했고 얼마나 거부당했는지. `-` 는 미인증/인증 실패입니다.
""")
    for n_, r in enumerate(sorted(d.pri, key=lambda r: -r.get("requests", 0))[:4], 1):
        w(f"#### 8.{n_} `{r.get('user_principal_name')}` — {r.get('requests')} requests, {r.get('auth_denied',0)} denied\n")
        w(block(r, REPORT_ORDER) + "\n")

    errrow = pick(d.res, resource="__errors__")
    rolerow = next((r for r in d.res if r.get("resource_kind") in ("catalog-role", "principal-role") and r.get("errors", 0) > 0), None)
    normal = next((r for r in sorted(d.res, key=lambda r: -r.get("requests", 0)) if r.get("resource") != "__errors__"), None)
    commit = next((r for r in d.res if r.get("commit_count")), None)
    w("""---

## 9. 요약 — resource

리소스(경로) 별 한 행. **무엇이** 얼마나 불렸고 얼마나 실패했는지.

세 가지 특수 행을 알아두면 읽기 쉽습니다:

| 행 | 뜻 |
|---|---|
| `__errors__` | **오류 요청은 새 리소스 행을 만들지 못합니다** (`create=false` — 없는 테이블 이름을 두드리는 클라이언트가 키 공간을 채우지 못하게). 같은 윈도우에서 그 경로의 성공 요청이 먼저 오지 않았다면, 오류는 전부 이 한 행으로 모입니다. **개수는 보존되고 귀속만 사라집니다** |
| `__other__` | 리소스 행이 상한(500)을 넘겼을 때 넘친 요청이 모이는 행. 이 export 에는 없습니다 |
| 롤 행 (`catalog-role` / `principal-role`) | 예외적으로 **오류로도 행을 만듭니다** — 거부된 grant 가 곧 롤 행이 답해야 할 보안 질문이기 때문. 상한은 별도(100), 넘긴 개수는 `summary.role_keys_forced` |
""")
    n_ = 0
    for title, r in [("일반 리소스 행", normal), ("롤 행 — 거부된 요청이 만든 행", rolerow),
                     ("`__errors__` — 귀속되지 못한 오류", errrow), ("커밋 시간이 붙은 행", commit)]:
        if not r: continue
        n_ += 1
        w(f"#### 9.{n_} {title} — `{r.get('resource')}`\n")
        w(block(r, REPORT_ORDER) + "\n")

    w(f"""---

## 10. 요약 — app_dropped

허용 목록(`APP_ALLOW`) 밖이라 **버린** 애플리케이션 로그를, logger 별로 몇 줄 버렸는지만 남깁니다. 추이 지표가 아니라 **헬스 신호**입니다: 여기에 새 `org.apache.polaris.service.*` 가 보이면 허용 목록을 검토하라는 뜻입니다.

이 export 의 버린 줄 합계는 {dropped}건입니다.
""")
    agg = collections.Counter()
    for r in d.drop: agg[r.get("logger_name")] += r.get("dropped", 0)
    w("| logger | 버린 줄 |\n|---|---|")
    for lg, c in agg.most_common():
        w(f"| `{lg}` | {c} |")
    w("")
    if d.drop:
        w("#### 10.1 행 하나의 모양\n")
        w(block(sorted(d.drop, key=lambda r: -r.get("dropped", 0))[0], REPORT_ORDER) + "\n")

    pex = pick(d.access, http_status=403) or (d.access[0] if d.access else {})
    rid_ex = (pex.get("mdc") or {}).get("requestId", "")
    prin_ex = next((r.get("user_principal_name") for r in d.pri if r.get("auth_denied", 0) > 0 and r.get("user_principal_name") != "-"), "-")
    w(f"""---

## 11. 검색 쿼리 예시 (DQL)

> **문자열 필드는 `.keyword` 로 검색합니다.** v6 인덱스 템플릿부터 선언되지 않은 문자열은 `.keyword` 에만 색인되고, 필드명만 쓰면 새 인덱스에서 0건이 나옵니다. `.keyword` 는 이전 인덱스에도 있으므로 아래 쿼리는 전 기간에 그대로 동작합니다. 숫자·`message`(전문 검색) 는 필드명 그대로 씁니다.
>
> **`threadName` 이 특히 함정입니다** — 2026-09-18 에 복원됐지만 명시적 매핑이 없어서 `text`(index:false) + `.keyword` 입니다. `threadName:"executor-thread-16"` 은 **항상 0건**입니다. `threadId` 는 `long` 이라 그대로 씁니다.

```text
# 상세 — polaris-logs-*
loggerName.keyword:"io.quarkus.http.access-log"
loggerName.keyword:"io.quarkus.http.access-log" and http_status >= 500
http_status:401 or http_status:403
user_principal_name.keyword:"{prin_ex}"
level.keyword:"ERROR" and exception.exceptionType.keyword:*
mdc.requestId.keyword:"{rid_ex}"
loggerName.keyword:"org.apache.polaris.service.admin.PolarisServiceImpl"
threadName.keyword:"executor-thread-16"          # 맨 이름으로 쓰면 0건
threadId:57
message:"Adding grant"
secret_redacted:true
access_log_parse_error:true

# 요약 — polaris-report-*
report_type.keyword:"summary"
report_type.keyword:"summary" and (errors_5xx > 0 or auth_denied > 0 or counted_404 > 0)
report_type.keyword:"principal" and window_start.keyword:"{busy.get('window_start')}"
report_type.keyword:"resource" and errors_5xx > 0
report_type.keyword:"resource" and resource.keyword:"__errors__"
report_type.keyword:"resource" and commit_count > 0
report_type.keyword:"app_dropped"
report_type.keyword:"summary" and partial_window.keyword:"true"
```

**조사 순서**: `report_type:summary` 로 이상 윈도우 발견 (`errors_5xx`, `auth_denied`, `counted_404` 급증) → 같은 `window_start` 의 `principal` / `resource` 행으로 범위 좁히기 → 그 시간대 상세 인덱스에서 실패 요청 찾기 → `mdc.requestId` 로 예외 · 스택 트레이스 · 서비스 로그 확인. 성공한 조회와 404 는 상세 인덱스에 없으므로 **요약 행의 숫자가 그 요청들의 유일한 기록**입니다.

**5xx 를 조사할 때 하나 더**: `resource` 행에 5xx 가 안 보이는데 `summary.errors_5xx` 는 0 이 아닐 수 있습니다. 그 오류는 `__errors__` 행에 있습니다 (§9) — 같은 윈도우에 그 경로의 성공 요청이 없었다는 뜻입니다.

---

*생성: `{' '.join(argv)}` · 상세 {len(d.detail)}건 / 요약 {len(d.report)}건 · 스키마 v{d.report[0].get('schema_version') if d.report else '?'}*
""")
    return "\n".join(P)

def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    d = Data(load(sys.argv[1]), load(sys.argv[2]))
    if not d.detail or not d.report:
        sys.exit("empty export: need hits in both files")
    vers = {r.get("schema_version") for r in d.report}
    if vers != {6}:
        print(f"WARNING: report schema_version(s) {sorted(vers)} -- this generator writes a v6 document",
              file=sys.stderr)
    sys.stdout.write(emit(d, ["step14-sample-doc.py"] + [a.split("/")[-1] for a in sys.argv[1:]]))

if __name__ == "__main__":
    main()
