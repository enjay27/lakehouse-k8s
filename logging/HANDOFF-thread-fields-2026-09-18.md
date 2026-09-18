# HANDOFF — restore `threadName` / `threadId` to `polaris-logs-*`

**2026-09-18. Written to be read cold.** Supersedes
[`HANDOFF-pipeline-next-2026-09-16.md`](HANDOFF-pipeline-next-2026-09-16.md) as the start-here
document for `logging/`; that file's state section is now two Polaris versions out of date.

**Nothing in this document has been applied.** Prepared in a Cowork session with no `kubectl`,
`helm` or `docker` reach (CLAUDE.md).

---

## Context: what changed under the pipeline while it was not looking

Polaris was upgraded **1.3.0-incubating → 1.6.0** on 2026-09-18 and the metastore migrated
**schema v3 → v4**. The pipeline survived it: **console output is still JSON**
(`QUARKUS_LOG_CONSOLE_JSON_ENABLED` is intact), so tier 2 and report schema v6 keep parsing.
Verified from `kubectl logs` — see [`../polaris/RUNBOOK-upgrade-1.6.0.md`](../polaris/RUNBOOK-upgrade-1.6.0.md)
step 5.

Two things from that upgrade bear on any pipeline work from here:

- **`#38` — Polaris no longer writes a log file at all.** `quarkus.log.file.enabled=false`, and
  the running container has no `QUARKUS_LOG_FILE_ENABLED` to override it. `/deployments/logs/`
  still holds `polaris.log` and ~130 rotated `.gz` back to Aug 21, but nothing has been written
  since **01:35 on 2026-09-18**. **So `fb-polaris-shipper` now tails a file that never
  changes.** It had real content until today — that is a correction to an earlier claim in this
  repo — but from here it delivers nothing. Uninstalling it loses nothing going forward.
- **`#39` — the HPA moves the replica count on its own.** It scaled `1 → 3 → 2 → 1` within an
  hour on **memory at 2% CPU**, because memory utilisation is measured against the `1Gi`
  request while the JVM commits `1Gi` of initial heap. Resting state is 1. **Any before/after
  byte comparison in this document must record the replica count at both readings**, or a
  measured difference may just be a different number of writers.

---

## The task

**Restore `threadName` and `threadId` to `polaris-logs-*`.** They were removed on 2026-09-16
(`#30`) and Kade has asked for them back.

### One correction to the premise, because it changes the trade-off rather than cancelling it

The request came with the reasoning: *"I thought this parameter is parsed by a function in the
Lua script, so I requested removal. But threadId and threadName don't cost CPU to ship to
`polaris-logs-*`, so restore them."*

**Half right, and the wrong half matters.**

- **Correct: the Lua never parsed them.** It reads only `loggerName`, `level`, `message`,
  `_time` and `mdc`. They were dropped by a `record_modifier`, not by Lua logic — see
  `5315e0d` ("trimmed in FILTER 4, not in the Lua").
- **Not correct: shipping them is free.** `polaris_field_trim` runs **before** the Lua filter,
  deliberately. `REVIEW-pipeline-2026-09-16.md` P1 moved the trim ahead of the Lua precisely
  because **the Lua converts the whole record into a Lua table and back on every line**, so
  every surviving field is paid for in that conversion whether the Lua reads it or not. The
  seven fields moved ahead of the Lua were measured at **~32% of record bytes**.

So restoring two of those seven puts their share of both the conversion cost and the index
bytes back. Their individual share was **never measured separately** — which makes the
before/after measurement below the point of the exercise, not a formality. The decision is
still Kade's; it is a cost/value trade, not a free change.

### `ndc` — leave it removed

`ndc` is in the same `Remove_key` list but is **not** part of this request, and it should stay
out: it was `""` in all 300 detail documents sampled on 2026-09-16, and it is `""` in the
1.6.0 console output too. Restoring it would add an always-empty field to every document.

---

## What to change

### 1. `fluent-bit/values.yaml` — the `polaris_field_trim` filter

```
    [FILTER]
        Name          record_modifier
        Alias         polaris_field_trim
        Match         polaris.logs
        Remove_key    processName
        Remove_key    loggerClassName
        Remove_key    processId
        Remove_key    logtag
        Remove_key    time
        Remove_key    stream
        Remove_key    threadName      <- delete this line
        Remove_key    threadId        <- delete this line
        Remove_key    ndc             <- KEEP
```

Update the Korean comment above it in the same edit: it currently states the 2026-09-16
decision ("스레드 이름·ID 는 추적 가치가 없어 제거"), which becomes false the moment the lines
go. Say what was decided and when, and that `ndc` stays out for a different reason.

**Tier 1 and the shipper are unaffected.** `polaris_field_trim` matches `polaris.logs` only, so
`k8s-logs-*` has always carried these fields and still will.

### 2. `logging/opensearch/polaris-logs-template.json` — restore the `threadId` mapping

The template records its own removal:

> `"removed_2026-09-16": "threadId mapping dropped: threadName, threadId and ndc are removed by
> polaris_field_trim (fluent-bit/values.yaml FILTER 4). Indices created before the upgrade still
> hold them."`

Put the explicit `threadId` integer mapping back and update that note. `threadId` arrives as a
JSON integer so dynamic mapping would probably reach `long` on its own — but the template exists
because *"each daily index's field types are decided by chance"* depending on which document
arrives first, and an explicit mapping is the whole point of the file.

**`threadName` needs no mapping and must not get one**, but note the consequence: as an
undeclared string it falls to `dynamic_templates.strings_keyword_only`, i.e. **`text` with
`index:false` plus a `.keyword` sub-field**. So

> **query `threadName.keyword`, never bare `threadName`.** A `term`, `exists` or `match` on the
> bare field finds nothing. This is the v6 caveat already recorded in the template and it will
> bite whoever first tries to filter by thread.

### 3. Apply it — values-only path, **not** `apply-lua.sh`

The Lua is not being touched, so this is the **values-only** rule from `MEMORY.md`:

```
step2  →  helm upgrade  →  step3
```

`apply-lua.sh` is for Lua changes and would restart Fluent Bit for no reason. **If you also
land the `WINDOW_SECONDS 30 → 1800` change** that `MEMORY.md` lists as next, that *is* a Lua
change and the two together take the third path — `apply-lua.sh --no-restart` → `step2` →
`helm upgrade`, with **no restart in between**. Doing either half alone stops every input or
stores every access line as a parse error (`#31`). **Prefer landing them separately**, so the
byte measurement below attributes cleanly.

### 4. The index template only affects **new** indices

Applying the template does not touch today's `polaris-logs-YYYY.MM.DD`. The `threadId`
mapping arrives with the next daily index. Until then `threadId` is whatever dynamic mapping
chose in the current index — and in indices created between 2026-09-16 and this change, the
field is simply absent.

---

## Verification

`#30` was verified by the assertion *"0 of 386 `polaris-logs-*` docs carry `threadName`,
`threadId` or `ndc` after revision 19"*. Invert it, and measure the cost at the same time.

1. **Confirm the filter shipped**, from the running object and not the values file
   (CLAUDE.md): read the ConfigMap Fluent Bit actually loaded and check the two `Remove_key`
   lines are gone.
2. **Roll a window** and use `scripts/step10` + `step11` for the readout — **not** Dev Tools
   copies (`MEMORY.md`).
3. **Assert the reverse of `#30`:** every detail document carries `threadName` and `threadId`,
   and **none** carries `ndc`. Use `threadName.keyword` for the `exists`/`term`.
4. **Measure the cost**, which is the reason this is worth doing carefully:
   - average detail-document size before and after, from the same query shape;
   - Fluent Bit's Lua filter CPU, the metric `REVIEW-lua-refactor-2026-09-16.md` used to show
     the refactor was 2.8× cheaper — the comparable figure here;
   - **record the replica count at both readings** (`#39`).
5. If the byte increase is larger than the value of the fields, that is a real answer and the
   change can be reverted by restoring the two lines. Say so in the commit either way.

---

## Also open, and none of it blocks this

| ref | one line |
|---|---|
| **`#41`** | a 1.6.0 pod crashed 3× at rollout — `Reason: Error`, exit 1, dead in **4 s**, **not** an OOMKill. `kubectl logs <pod> --previous`, or the `k8s-logs-*` Dev Tools query in `../polaris/RUNBOOK-upgrade-1.6.0.md`. **Perishable** — `#39` recycles pods |
| **`#39`** | the HPA flaps on memory at 2% CPU. **Pin `replicaCount` / disable autoscaling before any `#15` ladder run**, or hypothesis C is intermittently live and the run is irreproducible |
| **`#40`** | rotation suffixes reach `.14` against `maxBackupIndex: 5`, with same-size bursts minutes apart. Either inert rotation config or `#8` already bit. `exec -- cat *.gz` out and check for two `hostName` values (**no `zcat` in the image**) |
| **`#37`** | the Polaris chart's `pre-upgrade` hook pulls `bitnami/kubectl:latest` with no `imagePullPolicy`, from Bitnami's retired public catalog. Green today; re-pulls on **every** upgrade. Known-good digest filed for pinning |
| **`#36`** | v3's four table comments are absent from the live metastore; `schema.sql` is `schema_v3.sql` minus its 24 comments. No structural risk |
| **shipper** | `fb-polaris-shipper` still installed, age 27d, now tailing a file nothing writes (`#38`) |
| **P5** | still undecided (`REVIEW-pipeline-2026-09-16.md`) |
| **secret** | `fluent-bit/values.yaml` carries a **plaintext OpenSearch admin password** in the `[OUTPUT]` blocks, against CLAUDE.md's *Zero Hardcoded Credentials*. Not this task, but it is in the file being edited — worth its own change, rotating the credential rather than only moving it |

**ISM / retention remain the Monitoring team's** (2026-09-16), not ours.
