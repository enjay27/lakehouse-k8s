# HANDOFF — restore `threadName` / `threadId` to `polaris-logs-*`

**2026-09-18. Written to be read cold.** Supersedes
[`HANDOFF-pipeline-next-2026-09-16.md`](HANDOFF-pipeline-next-2026-09-16.md) as the start-here
document for `logging/`; that file's state section is now two Polaris versions out of date.

**STATUS 2026-09-18 (final): decision B taken, ROLLED, and VERIFIED ON TRAFFIC. This task is
DONE.** step3 after traffic: **367/367 detail docs carry `threadName.keyword` and `threadId`,
0 carry `ndc`** — the exact inverse of `#30`'s assertion. Pod started 07:23:34Z on image 5.1.1,
tier-2 output `ok=367 errors=0`, Lua ConfigMap sha unchanged (values-only, as planned). Full
record: `.memory/active-issues.md` `#42`.

**Still open from the roll:** `step12`'s output was not read, so it is unknown whether the index
template was applied — if it was not, tomorrow's index is shaped by dynamic mapping again. Also
unread: the helm revision (expect 21) and `step10`/`step11`.

Everything below is kept as the reasoning behind the change, not as instructions to carry out.

**Two things changed in this document after the decision:** the cost is now quantified (it did
not need a cluster), and the before/after measurement in *Verification* is **withdrawn** — worked
through, it cannot deliver the number it promised. Both are below, and the full record is
`.memory/active-issues.md` `#42`.

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
bytes back.

**Correction to this document's own claim: the individual share HAD effectively been measured.**
P1's table breaks the 717 B pre-trim record down per key, and the two fields are in it:
`threadName` **4.7 % ≈ 34 B**, `threadId` **≈ 13 B** (inside the 4.7 % it shares with
`processId` and `ndc`). Both check out against the literal JSON —
`"threadName":"executor-thread-3",` is 33 B, `"threadId":46,` is 14 B. So:

- **stored detail doc +47 B: +7.2 % (access, 649 B) / +6.3 % (app, 743 B)** — almost exactly the
  −7…8 % schema v6 bought (`#32`). **This change hands back the v6 document-size win.**
- **into the Lua: ~488 B / 9 keys → ~535 B / 11 keys (+9.6 % bytes, +22 % keys)** on every one of
  the ~720 records per window.
- on disk it is less than that: `threadName` becomes one keyword index over ~5 distinct values,
  and `_source` is compressed. The `_source` figure is the ceiling, not the disk number.

**DECIDED (Kade, 2026-09-18): option B — restore both fields, as written below.** Taken with
those numbers in hand. An option A (`threadName` only, 34 B, no template edit, `threadId` being
strictly 1:1 with `threadName` in every sample in this repo) was offered and declined.

**What it buys, since the original premise doesn't carry it:** `mdc.requestId` is already the
per-request key, so the value is elsewhere — records with **no MDC at all** (start-up,
background, pool/JVM logs) have no other correlation handle in tier 2; and tier 1 carries the
thread fields but not `api_path` / `http_status` / `user_principal_name`, so *"which thread
served the 404s for principal X"* is answerable in **tier 2 only**.

### `ndc` — leave it removed

`ndc` is in the same `Remove_key` list but is **not** part of this request, and it should stay
out: it was `""` in all 300 detail documents sampled on 2026-09-16, and it is `""` in the
1.6.0 console output too. Restoring it would add an always-empty field to every document.

---

## What to change

### 1. `fluent-bit/values.yaml` — the `polaris_field_trim` filter — **DONE**

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

The Korean comment above it was rewritten in the same edit — it stated the 2026-09-16 decision
("스레드 이름·ID 는 추적 가치가 없어 제거"), which went false the moment the lines did. It now
carries the 2026-09-18 decision, the accepted byte cost, and `ndc`'s separate reason for staying
out.

**A step this document did not list, and it would have broken the roll: the `#30` verification
gates had to be INVERTED.** `step2-render-gate.sh` asserted `Remove_key threadName` and
`Remove_key threadId` were each present exactly **1** time; `step3-postupgrade.sh` asserted **0**
docs carried either field since pod start. Left alone, both would have FAILED on a correct
change — and step2 is the gate in front of `helm upgrade`. Now: step2 expects **0** for the two
lines (kept as counts rather than deleted, so a silent reappearance is still caught) and 1 for
`ndc`; step3 drops them from its absence loop and asserts them **present** instead.
`step12` needed no change — it iterates the file's declared fields, so it picks up `threadId` by
itself and should report **8/8** where `#30` recorded 7/7.

**Tier 1 and the shipper are unaffected.** `polaris_field_trim` matches `polaris.logs` only, so
`k8s-logs-*` has always carried these fields and still will.

### 2. `logging/opensearch/polaris-logs-template.json` — restore the `threadId` mapping — **DONE**

The template records its own removal:

> `"removed_2026-09-16": "threadId mapping dropped: threadName, threadId and ndc are removed by
> polaris_field_trim (fluent-bit/values.yaml FILTER 4). Indices created before the upgrade still
> hold them."`

**DONE.** The explicit `threadId: long` mapping is back, `_meta.removed_2026-09-16` is replaced
by `_meta.restored_2026-09-18`, and `measured_from` no longer reads "(removed 2026-09-16)".

**Correction while doing it: this mapping is defensive, not load-bearing.** `threadId` arrives as
a JSON integer and `dynamic_templates.strings_keyword_only` matches `match_mapping_type: string`
only — so dynamic mapping reaches `long` unaided, and nothing breaks without the declaration. It
is declared because the template exists so that *"each daily index's field types are decided by
chance"* is not true, which is a good enough reason on its own; but it is not what makes the
change safe, and this document previously implied it was.

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
   and **none** carries `ndc`. Use `threadName.keyword` for the `exists`/`term` — the bare field
   finds nothing. **`step3` now does this for you**: the two fields moved out of its absence loop
   into a presence check that names `threadName.keyword` and bare `threadId` (mapped `long`).
4. ~~**Measure the cost**~~ — **WITHDRAWN 2026-09-18.** This was written as "the point of the
   exercise." Worked through before rolling, it cannot deliver what it promised, and the
   reasoning is worth keeping so nobody re-proposes it:
   - **`_source` bytes** — already derived to within ~5 B from P1's per-key table (+47 B/doc,
     above). A live before/after reproduces a known number while fighting `#39`'s replica
     flapping, which is why this document demanded the replica count at both readings in the
     first place.
   - **On-disk store size** — *not obtainable on a same-day roll at all.* The index template
     shapes only **tomorrow's** index, so before- and after-shaped documents land in the **same**
     daily index, and `_index/_stats` store size cannot be attributed to a subset of its
     documents. A trustworthy figure needs a full day's separation.
   - **Lua filter CPU** — out of reach by `REVIEW-pipeline` P1's own words (*"Cannot be measured
     from Cowork: CPU. It is a phase 3.1 load-test number."*). Worse, `helm upgrade` restarts
     Fluent Bit, so the first window after the roll is `#31`'s R4 partial window and unusable as
     the "after" reading regardless.

   So this was settled as **decide-then-accept-47 B**, not measure-then-decide. Building the
   scaffolding would have cost more than the information it could produce.
5. **The revert is still one edit**, if the fields turn out not to earn their 7 %: restore the
   two `Remove_key` lines and re-invert the two gates. The cost is known in advance, so that
   decision does not need a measurement either — it needs someone to have tried querying
   `threadName.keyword` for a month and found they never did.

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
