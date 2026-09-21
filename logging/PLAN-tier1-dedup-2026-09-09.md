# PLAN — `#18`: give tier 1 a dedup key that works. **Needs a decision before any edit.**

**Status: PROPOSED, nothing changed.** Kade asked for dedup on 2026-09-09. *Whether* to dedup is
settled; *how* is a fork with a dangerous failure mode, so it is presented rather than chosen.

## Where things actually stand

`Id_Key sequence` on OUTPUT 1 has **never once worked**. Polaris emits `sequence` as a JSON
integer; the OpenSearch plugin requires the `Id_Key` value to be a **string** and drops the record
instead — continuously, in the pod log, since the day it was configured. Measured 2026-09-09:
13,737 documents over 13,737 distinct `sequence`, ratio **1.000**, busiest buckets one document
each. So:

- **OUTPUT 1 indexes nothing.** Every Polaris document in `k8s-logs` comes from OUTPUT 2 alone,
  with `Generate_ID On` — a fresh `_id` per attempt, i.e. no dedup at all.
- `#16`'s "every line exists twice" was disproved by the same measurement.
- A retried chunk therefore duplicates. `#19` was producing exactly those retries until REVISION 10.

## The trap that governs every option below

**`Id_Key` naming a field the record does not have makes the plugin DROP the record.** That is
precisely the bug being fixed. OUTPUT 2 matches `kube.*` — *every pod on the node*, DataHub and
PostgreSQL included — and only Polaris records carry `sequence`. **Putting `Id_Key sequence` on
OUTPUT 2 would silently discard every non-Polaris log on the node.** Any option that touches
OUTPUT 2's `Id_Key` must guarantee the key exists on 100% of records reaching it.

And `sequence` is a poor key even where it exists: it is a **per-JVM counter from JVM start**, so it
resets on every Polaris restart, and `#8`'s HPA replicas would each run their own. Two records from
different pod generations can collide on the same value. With `Write_Operation upsert` a collision
does not overwrite — `doc_as_upsert` **field-unions two unrelated log lines** into one document
that never existed.

## Option A — composed key, Polaris only *(recommended)*

Add a small Lua filter on the Polaris tags that composes a string id from parts that are stable
across restarts, then key OUTPUT 1 on it and **delete OUTPUT 2's claim on Polaris records**.

```
_doc_id = hostName .. ":" .. sequence .. ":" .. timestamp
```

`hostName` distinguishes pod generations and HPA replicas; `timestamp` disambiguates a `sequence`
that has reset. All three are already on the record after the parse.

- **Pro:** real idempotency; survives restarts and replicas; the collision that produces a
  fictional field-union becomes impossible.
- **Con:** requires OUTPUT 2 to stop matching Polaris, which Fluent Bit cannot express as an
  exclusion — the tag has to change, or OUTPUT 1 has to become the only Polaris output. **This is
  the real work in this option** and it touches tier 1's routing.
- New Lua goes in **its own `luaScripts` key**, not in `polaris_access_log.lua`. That file is the
  policy filter and its sha is a verification artifact.

## Option B — drop OUTPUT 1, accept no dedup *(honest, zero risk)*

Delete OUTPUT 1 entirely. It indexes nothing; removing it changes no observable behaviour and
deletes a block that has been misleading readers since it was written.

- **Pro:** the config finally describes what runs. No blast radius at all.
- **Con:** does not give you what you asked for. `k8s-logs` keeps duplicating on retry.
- Worth noting: with `#19` fixed, retries are now rare — the duplication path is mostly closed by
  removing its *cause* rather than its *effect*.

## Option C — coerce `sequence` to a string, keep everything else

A `modify`/Lua step copies `sequence` into a string field; OUTPUT 1 keys on that.

- **Pro:** smallest diff.
- **Con:** keeps a per-JVM counter as an identity across restarts and replicas, which is the
  original design error. It would make the `upsert` field-union hazard **live** — it is currently
  dormant only because nothing is ever indexed by OUTPUT 1. **Not recommended.**

## Recommendation

**A**, with **B** as the honest fallback if the OUTPUT 2 routing change is judged too invasive for
tier 1 right now. C makes a dormant hazard live and should not be chosen for its diff size.

## Gate, whichever is chosen

Ratio must stay at **1.000**, measured **under load**:

```bash
bash logging/scripts/step7-dedup-check.sh
```

Then the part that actually tests the fix — a duplicate can only appear on a **retry**, so
provoke one or confirm from the metrics that retries occurred and the count still holds:

```bash
curl -s localhost:2021/api/v1/metrics | jq '.output'   # retries_total > 0 in the window?
```

**A ratio of 1.000 with zero retries in the window proves nothing about dedup** — it is the idle
reading again. That is the whole lesson of `#19`'s baseline.

And after any `Id_Key` change, count documents from a **non-Polaris** pod before and after:

```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/k8s-logs-*/_count" -H 'Content-Type: application/json' \
  -d '{"query":{"bool":{"must_not":[{"exists":{"field":"sequence"}}]}}}'
```
A drop here is the failure mode this whole plan exists to avoid, and it is silent everywhere else.

## Not verifiable from a Cowork session
No `helm lint`, no `--dry-run`, no cluster reach.
