# PLAN — retire VictoriaLogs; ship the Polaris pipeline into the existing OpenSearch

**Written 2026-09-08. Plan only — no values file has been edited. Nothing here is deployed.**

## The decision, as taken

Kade, 2026-09-08:

1. **VictoriaLogs is not necessary.** The existing OpenSearch (Docker on the Mac,
   `192.168.194.1:9200`) is the sink, under a **new index**.
2. **No new Fluent Bit is to be deployed** — "just add configs for new index in OpenSearch".

Point 2 is already satisfied by the smallest possible change, and this plan takes it that way:
**`fb-polaris-shipper` is an existing release, not a new one.** It keeps its own Deployment
release and its own values file; only its `[OUTPUT]` block and one rename change. Nothing new is
installed, and the DaemonSet release (`fluent-bit/values.yaml`, node-wide container stdout →
`k8s-logs`) is not touched at all.

**Folding the shipper into the DaemonSet was considered and rejected**, and the reason should
survive this document: the DaemonSet runs Fluent Bit **3.2.2**, the shipper runs **5.1.1**.
Merging forces a version decision underneath a Lua filter chain whose failure mode — #13 — was
*a disabled filter that looked like a success from outside*. It would also put the report's
per-instance Lua window state in a per-node DaemonSet, and make a shipper edit capable of
breaking node-wide log collection. Two releases, one sink.

Also settled at the same time:

- **Two indices**, not one: `polaris-logs-*` and `polaris-report-*`.
- **Dual-write one window, reconcile, then drop the VictoriaLogs output.**

---

## 1. Does this change a lot, or a bit? — a bit of pipeline, a lot of query layer

This is the question worth answering before any work starts, because the two halves have very
different sizes and only one of them is in this repo.

| | size | where |
|---|---|---|
| **The data plane** | **~40 lines** — one OUTPUT block replaced, one rename filter added, one index template written | `logging/fb-values.yaml` |
| **The query layer** | **~20 LogsQL recipes + the harness's collection step, all rewritten** | guide §7, the notebook, `polaris-practice/polaris-learning/` — **not mounted here** |
| **The docs** | **~40% of a 958-line guide**, plus 6 other files | this repo |

**Nothing about what is collected or what is kept changes.** Polaris config, the PVC, the tail
INPUT, the access-log Lua parser, noise-filter policy **v3**, report schema **v2**, the window
arithmetic, carry-and-decay, `type_int_key` — every one of those is storage-agnostic and comes
across untouched. The filter chain is the asset; only the last hop moves.

**But the sharp edges are all on the query side**, and three of them produce *a plausible wrong
number rather than an error* — the exact failure mode this pipeline has now hit three times
(`type_int_key`, #13, harness bug 1). They are §3 below. Do not treat this as a one-line change
because the OUTPUT block is one block.

---

## 2. What actually changes in the pipeline

### 2.1 The OUTPUT — two of them, tag-routed

`Match polaris.*` becomes two matches, which is what replaces `_stream_fields=app,level`. The
VictoriaLogs stream selector had no OpenSearch equivalent; index routing is the equivalent, and
it is better, because the two now get **separate retention** (§2.4).

```ini
[OUTPUT]
    Name                opensearch
    Match               polaris.vlogs           # rename the tag too — see §6 open Q1
    Host                192.168.194.1
    Port                9200
    HTTP_User           ${OS_USER}              # NOT a literal — see §3.6
    HTTP_Passwd         ${OS_PASSWORD}
    Logstash_Format     On
    Logstash_Prefix     polaris-logs
    Logstash_DateFormat %Y.%m.%d
    Time_Key            @timestamp
    Suppress_Type_Name  On
    tls                 On
    tls.verify          Off
    Id_Key              sequence                # ← replay becomes idempotent. See §3.5
    Write_Operation     upsert
    Retry_Limit              5
    storage.total_limit_size 1G

[OUTPUT]
    Name                opensearch
    Match               polaris.report
    ... Logstash_Prefix polaris-report
    Generate_ID         On                      # reports carry no `sequence` — see §3.5
```

`json_date_key false` has no counterpart and goes away; the `date`-key duplication it suppressed
was a VictoriaLogs-specific artifact.

### 2.2 The `_msg` / `_time` rename must be undone at the far end, not at the near end

Filter 1 renames `message → _msg` and `timestamp → _time` **because VictoriaLogs reserves those
names**. In OpenSearch they are ordinary fields with an ugly leading underscore, and `_time` is
*not* the time field.

**Do not fix this by changing filter 1.** Filters 2 and 3 both read `_msg`, and filter 3's Lua
writes `_msg` on every report row (`e._msg = string.format(...)`). Changing filter 1 means
editing the Lua, which means re-verifying the whole chain and invalidating the notebook's sha
gate for no gain.

**Fix it as a fifth filter, after the noise filter**, so the Lua contract is untouched:

```ini
[FILTER]
    Name          modify
    Alias         polaris_opensearch_keys
    Match         polaris.*
    Rename        _msg  message
    Rename        _time @timestamp
```

Order matters and is a contract, same as §4.4 of the guide: **filter 5 runs last**, after
`polaris_field_trim`.

### 2.3 An explicit index template — the single largest risk, and it is a mapping risk

VictoriaLogs is schemaless and types per field on the fly. OpenSearch **locks a field's type on
first write, per index**, and defaults every string to `text` + a `.keyword` sub-field. Three
consequences, each of which silently returns a wrong answer:

- **`stats by (loggerName)` becomes a terms agg on `loggerName.keyword`.** On `loggerName`
  itself it aggregates *analysed tokens* — `org`, `apache`, `polaris`, … — and returns a
  plausible, completely wrong histogram. Every `stats by (...)` recipe in guide §7 is affected.
- **A number that arrives once as a string or a double locks that way.** `type_int_key` already
  exists precisely because Fluent Bit encoded `404.0` and numeric LogsQL filters missed it. In
  OpenSearch the same event locks `http_status` as `float` **for the life of the index**, and a
  later `long` write is coerced or rejected. The report's ~25 counters have the same exposure —
  and a `float` sum over large `bytes_total` values loses precision.
- **Dynamic field growth.** `mdc.*` and `exception.*` expand under dynamic mapping; the default
  `index.mapping.total_fields.limit` is 1000.

**Therefore: write the templates before the first document is indexed.** Two templates
(`polaris-logs-*`, `polaris-report-*`), with:

- explicit `long` for `http_status`, `response_size`, and every field named in the filter-3
  `type_int_key` list — that list is the authoritative inventory of what must be numeric, copy it;
- `dynamic_templates` mapping strings to **`keyword`**, with `text` only for `message`;
- `@timestamp` as `date`;
- `boolean` for `access_log_parse_error`.

A template written after the first write does nothing to the index already created. This is the
one step that cannot be done late.

### 2.4 Retention — the chance to close #7

VictoriaLogs had **one global 30d retention and no disk cap**, which #7 flags as a live risk
(a full PV wedges the pod). ISM can express what VictoriaLogs could not, and the asymmetry
matters here specifically:

**Since policy v3, a successful read exists only as a report aggregate.** The report is not a
convenience view of the logs — for reads it is the *only* record. It should outlive them.

| index | retention | rationale |
|---|---|---|
| `polaris-logs-*` | 30d, with a rollover size cap | matches today; the cap is the #7 fix |
| `polaris-report-*` | **longer — 180d proposed** | the sole record of successful reads; tiny (48 rows/window) |

### 2.5 What is deleted

`logging/victoria-values.yaml`, and eventually the release. **Not in this change** — the dual-write
step keeps VictoriaLogs serving its 30d of history for lookback. `helm uninstall vlsingle` and the
50Gi PVC deletion are destructive and need separate authorisation at the moment of execution.

Note the knock-on: CLAUDE.md says the `logging` namespace exists to hold the log sink and is the
sole exception to strict `datahub-hynix` enforcement. When VictoriaLogs goes, **that exception has
no occupant** and the rule should be tightened rather than left dangling.

---

## 3. The sharp edges — six, and three return wrong numbers rather than errors

**3.1 `.keyword`.** §2.3. Every aggregation recipe. Wrong number, no error.

**3.2 The 10,000-hit cap.** LogsQL is queried with `limit=0` — unbounded — and the notebook's
step 6 pulls *every record for the run*. A plain OpenSearch `_search` **stops at 10,000 hits and
does not say so**. Must use `search_after` with a PIT, or `_count` first and assert. This is guide
§7.4 trap 1 (VM-UI truncating invisibly) reappearing in a new sink, and it will silently shrink a
coverage matrix.

**3.3 Refresh delay.** VictoriaLogs' ingest is async; OpenSearch's is async *and* has a refresh
interval (1s default) between "indexed" and "searchable". The existing advice — poll, do not
sleep-and-hope — still holds and now has two reasons.

**3.4 `sum()` on an empty group.** LogsQL returns `NaN` (§7.4 trap 5); OpenSearch returns `0.0`,
which is worse — it is indistinguishable from a real zero. **"Absence is not zero"** is the guide's
own closing lesson and OpenSearch removes the signal that made it visible. Every report aggregation
needs `value_count` beside `sum` from here on.

**3.5 Dedup — this one is a gain.** The guide records that a `helm upgrade` of the shipper replays
the whole log file (`Read_from_Head true`, tail DB on an `emptyDir`) and *"records can legitimately
appear twice — deduplicate by `mdc.requestId` when counting."* OpenSearch removes that caveat:
`Id_Key sequence` + `Write_Operation upsert` makes replay idempotent, exactly as the DaemonSet
already does for Polaris. Filter 4 deliberately keeps `sequence` for gap detection, so the key is
already there.

**Reports need a different key.** They come from the `dummy` INPUT and carry no `sequence`. Their
stable identity is `hostname + window_start + report_type + (resource | user_principal_name)` —
note **not** `report_seq`, which §7.4 trap 3 says is per-pod and resets. Either compose that key in
the Lua, or accept `Generate_ID On` and duplicate rows on replay. Recommend composing it: this is
the cheap moment to make the report stream replay-safe.

**3.6 The committed plaintext password.** `fluent-bit/values.yaml` carries
`HTTP_Passwd Str0ngP@ssw0rd123!` in the tree. That violates CLAUDE.md's Zero Hardcoded Credentials
rule today. **Do not copy it into `fb-values.yaml`.** The shipper takes the credential from a
Secret via env expansion (`${OS_USER}` / `${OS_PASSWORD}`), and fixing the DaemonSet's copy the
same way rides along as its own commit.

---

## 4. Sequencing — do the cutover *before* the harness fix, and use the fast window

The current state (MEMORY.md, 2026-09-07): report schema v2 is deployed and measured correct;
next up is the **harness**, which has 3 bugs, chiefly a window merge that does not sum v2 fields;
and the **temporary 30s window / 5s tick** is live and not yet reverted.

The obvious order is wrong. Two observations change it:

1. **The harness bugs are in code that queries the sink.** Fixing them against VictoriaLogs and
   then re-fixing them against OpenSearch is the same work twice. **Move the sink first, fix the
   harness once.** Bug 1's actual fix — *derive the summable set from the row's own numeric keys
   instead of a hardcoded list* — is sink-independent and gets more valuable here, because
   OpenSearch mappings punish hardcoded field lists the same way.
2. **The temporary 30s window is an asset for this migration, not just debt.** A verification run
   costs ~2 minutes at 30s and ~90 at 1800. Do the cutover and its reconciliation while it is
   still live; revert afterwards.

**Proposed order:**

| # | step | gate |
|---|---|---|
| 1 | Index templates written and PUT into OpenSearch | `GET _index_template/polaris-*` returns both; no `polaris-*` index exists yet |
| 2 | Filter 5 + the two OpenSearch OUTPUTs added **alongside** the existing http OUTPUT | `--dry-run --debug` render greps of guide §4.7, **plus** `grep -c 'Name  *opensearch'` == 2 and `Name  *http` == 1 |
| 3 | `helm upgrade`; read the pod log first | no Lua rejection, no crashloop; ConfigMap sha recorded |
| 4 | **Dual-write reconciliation — one window, ~2 min** | see §5 |
| 5 | Remove the http OUTPUT and filter 1's VictoriaLogs justification comment | render greps again; `Name  *http` == 0 |
| 6 | Harness + notebook collection layer ported to `_search` | a coverage run reproduces the run-`1788755035` arithmetic (158/41/12/1,186,348) **from OpenSearch** |
| 7 | Revert `WINDOW_SECONDS` 30→1800 and `Interval_Sec` 5→30, riding `resources_other` / `_distinct` into the summary `_msg` | `shipper-v3-upgrade-runbook.md` |
| 8 | ISM policies applied; VictoriaLogs uninstall proposed separately | — |

Steps 1–5 are one commit; 6 is another; 7 is the runbook's own.

---

## 5. The reconciliation gate — what "verified" means here

CLAUDE.md's Configuration Policy: *verify against the running object, never an intent artifact.*
For a sink change, the running object is the documents in both sinks. One window, both sides,
independently summed:

| assertion | why this one |
|---|---|
| `access_seen` on the summary row is **identical** in both sinks | the report is generated once and fanned out; a difference is a transport fault, not a filter fault |
| document count per window matches VictoriaLogs' `stats count()` for the same `start`/`end` | catches silent drops |
| `http_status` is queryable as a **number** in OpenSearch (`range: {gte: 500}` returns the 5xx) | the `type_int_key` / mapping trap, caught before history accumulates |
| `stats by (loggerName)` and the `.keyword` terms agg return the **same** group set | 3.1, caught explicitly rather than assumed |
| `errors_4xx` / `auth_denied` / `bytes_total` reconcile across resource rows, principal rows and summary | the v2 self-check that already passed on VictoriaLogs — it must still pass |
| a deliberate shipper restart produces **no duplicate** `sequence` in OpenSearch | proves 3.5 |

If the last one fails, `Id_Key` is not doing what this plan claims and the dedup caveat must be
carried over into the guide rather than deleted from it.

---

## 6. Open questions — settle before step 1

**Q1 — the tag `polaris.vlogs` is now a lie.** It is matched in three places (filter 1, filter 2,
filter 4) plus the OUTPUT, and it appears in the guide, the notebook and the architecture spec.
Rename to `polaris.logs` in the same commit, or leave it and add a comment? Renaming is cheap now
and gets more expensive with every document written. **Recommend renaming**, and note that the
noise filter's `Match polaris.*` — which is load-bearing, it is how the report tick reaches the
stateful instance — is unaffected either way.

**Q2 — does the DaemonSet already carry these Polaris lines?** It tails
`/var/log/containers/*benchmarks-polaris*` into `k8s-logs` **today**. If Polaris' console output
carries the access-log lines too, then `polaris-logs-*` and `k8s-logs` overlap, and the shipper's
value narrows to the *filtering and the report* rather than the collection. Worth one query before
building two retention policies over possibly-duplicated data. This is also #11 territory —
`logging.file.enabled: false` reads as off and the file is written anyway.

**Q3 — is `192.168.194.1:9200` reachable from a pod in `datahub-hynix`?** The DaemonSet reaches it
from the host network context. The shipper is a Deployment. **Assume nothing; test it** with a
throwaway `curl` from the shipper pod before the upgrade.

**Q4 — index-per-day at this volume.** `Logstash_DateFormat %Y.%m.%d` gives one index per day.
`polaris-report-*` writes ~48 tiny rows per window; a daily index for that is mostly overhead.
Consider a rollover alias for the report instead.

---

## 7. Documentation churn — the larger half of the work

**19 files mention VictoriaLogs.** The ones that state something that becomes *false*:

| file | what goes stale |
|---|---|
| `logging/POLARIS-LOGGING-GUIDE.ko.md` | §2.1 flow diagram, §2.2 the two-Fluent-Bit table, §2.3 inventory, §4.6 OUTPUT, **all of §5 (VictoriaLogs)**, **all of §7 (LogsQL → OpenSearch DSL)**, §8.2, §9.1 file map — roughly 40% of 958 lines |
| `CLAUDE.md` | Tech Stack (the shipper's sink, the VictoriaLogs line), and the `logging` namespace exception once it is empty |
| `MEMORY.md` | *Now* — this becomes the current work |
| `.memory/environments.md` | the 9428 line, the sink topology |
| `.memory/active-issues.md` | **#7 closes** (ISM gives the disk cap VictoriaLogs lacked); #2 and #5 both reference the sink |
| `logging/polaris-logging-architecture-spec.md` | §7 LogsQL recipes — the source the access-log field names were matched to |
| `POLARIS-API-LOG-COVERAGE-NOTEBOOK.md` | the limitations table (**4 of its 8 rows** change: the replay-duplicate caveat, the no-disk-cap row, the async-ingest row, and `_stream_fields`), step 6 collection |
| `POLARIS-LOG-COVERAGE-V3-HANDOFF.md`, `shipper-v3-upgrade-runbook.md` | the verification commands |

**Recommend: docs follow the reconciliation, not the edit.** Rewriting §7 against a query layer
that has not been run once is how a guide acquires recipes nobody has executed. Guide §5 and §7 get
rewritten in the step-6 commit, from queries that actually ran.

---

## What this plan does NOT authorise

No values file has been edited. Steps 1–8 above need explicit approval, and step 8's
`helm uninstall vlsingle` / PVC deletion needs its own authorisation **at the moment of execution**,
per CLAUDE.md — approval of this plan is not approval to run it.

**NOT VERIFIED: nothing here was checked against the cluster.** This is a Cowork session with no
`kubectl`, `helm` or `docker` reach. Every claim about the running state is read from the repo and
its memory tree, not from the objects.
