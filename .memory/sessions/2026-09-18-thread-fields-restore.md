# Session — restoring `threadName` / `threadId` to `polaris-logs-*` (2026-09-18, Cowork)

**Outcome: decision B taken, the change written and committed, nothing applied.** Filed as
`.memory/active-issues.md` `#42`. No cluster command was run at any point in this session —
no `helm`, no `kubectl`, no `docker` (CLAUDE.md's Cowork constraint).

Kade's opening instruction was not "do it" but **"before proceed, I need to check trade off of
this patch"**, and that framing is what produced everything useful here.

## The handoff asked for a measurement it could not have got

`HANDOFF-thread-fields-2026-09-18.md` made a before/after measurement "the point of the
exercise, not a formality," on the grounds that the two fields' individual byte share was
"never measured separately." Both halves of that turned out to be wrong, in opposite
directions.

**It had been measured.** `REVIEW-pipeline-2026-09-16.md` P1's table breaks the 717 B pre-trim
record down per key, and both fields are line items: `threadName` 4.7 % ≈ 34 B, `threadId`
≈ 13 B inside the 4.7 % it shares with `processId` and `ndc`. Checked against the literal JSON
(`"threadName":"executor-thread-3",` = 33 B, `"threadId":46,` = 14 B) they agree to a byte. The
answer the handoff wanted was already in the repo, one document away.

**And the part that wasn't derivable was not obtainable either.** Three components:

- `_source` bytes — derived above, ±5 B.
- on-disk store size — **impossible on a same-day roll.** The index template shapes only
  *tomorrow's* index, so before- and after-shaped documents land in the same daily index and
  `_index/_stats` cannot be attributed to a subset of them. Needs a full day's separation.
- Lua CPU — `REVIEW-pipeline` P1 already says it: *"Cannot be measured from Cowork: CPU. It is
  a phase 3.1 load-test number."* And `helm upgrade` restarts Fluent Bit, so the first window
  after the roll is `#31`'s R4 partial window and useless as the "after" reading anyway.

So the verification step that the handoff called the point of the exercise was **withdrawn**,
with the reasoning written into the document so nobody re-proposes it. The trade became
decide-then-accept-47 B.

**The number that made the decision concrete:** +47 B/doc is +7.2 % on an access doc (649 B)
and +6.3 % on an app doc (743 B) — almost exactly the −7…8 % schema v6 bought in `#32`. The
honest way to put it to Kade was *this change hands back the v6 document-size win*, and that is
what he decided against.

## The argument for the fields had to be rebuilt, because the one in the request was wrong

Kade's stated reasoning was *"they cost no CPU to ship."* They do — P1 moved the trim ahead of
the Lua precisely because the Lua round-trips every surviving field through a Lua table whether
it reads it or not. Presented with that, the request still stands, but on different grounds:

1. `mdc.requestId` is already the per-request key, so thread identity is not "tracing" in the
   ordinary sense. Its value is on records that have **no MDC at all** — start-up, background,
   pool and JVM-adjacent logs — where `threadName` is the only correlation handle in tier 2.
2. Tier 1 `k8s-logs-*` carries the thread fields on 870/870 records but has no `api_path`,
   `http_status` or `user_principal_name`. *"Which thread served the 404s for principal X"* is
   answerable in **tier 2 only.** That is the real justification and `#30` never weighed it.

## Offered A, got B, and B is slightly wasteful on purpose

`threadName` and `threadId` are strictly 1:1 in every sample in this repo
(`executor-thread-3`↔`44`, `-6`↔`48`, `vert.x-eventloop-thread-1`↔`33`, `-0`↔`32`), so option A
— name only, 34 B, no template edit — buys the whole diagnostic value at three-quarters the
cost. Kade took **B**, matching the handoff as written. Recorded rather than argued: the 13 B
difference is not worth a second round trip, and a redundant integer is a defensible thing to
want if you would rather not think about which of the two a future query needs.

## The step that would have broken the roll, and that no document listed

`#30` did not only remove the fields; it wrote assertions that they were gone, into the two
scripts that gate the roll:

- `step2-render-gate.sh` — `Remove_key threadName` and `Remove_key threadId` each present
  exactly **1** time.
- `step3-postupgrade.sh` — **0** docs carrying either field since pod start.

Both would have **FAILED on a correct change**, and step2 is the gate that runs *in front of*
`helm upgrade`. The handoff listed three steps — values, template, apply path — and none of
them was this. Inverted: step2 now expects 0 for the two lines (kept as counts rather than
deleted, so a silent reappearance is still caught) and 1 for `ndc`; step3 moves them out of its
absence loop into a presence check.

That presence check has a trap of its own. `threadName` gets no explicit mapping, so under the
v6 template it is `text` with `index:false` plus a `.keyword` sub-field — an `exists` on the
bare field finds nothing and would have failed the gate **for the wrong reason**, which is the
worst kind of failing gate. It names `threadName.keyword`. `threadId` is mapped `long`, so bare
is correct for it.

`step12` needed nothing: it iterates the template file's declared fields, so it picks `threadId`
up on its own and should report 8/8 where `#30` recorded 7/7.

## One more correction: the `threadId` mapping is insurance, not necessity

The handoff implied the explicit `threadId: long` mapping is what makes the change safe. It
isn't. `threadId` arrives as a JSON integer (template `_meta.measured_from`, 508-doc readout)
and `dynamic_templates.strings_keyword_only` matches `match_mapping_type: string` only, so
dynamic mapping reaches `long` unaided. The declaration is still right — the file exists so that
a daily index's types are not decided by whichever document happens to arrive first — but it is
belt-and-braces, and saying otherwise would have overstated it.

## A wrong turn worth recording

Mid-analysis I nearly reported that `threadId` arrives as a **string**, on the strength of
`"threadId": "46"` in `POLARIS-API-LOG-COVERAGE-NOTEBOOK.md` and `"sequence": "3724"` in the
2026-09-03 session. Both of those samples are **VictoriaLogs readouts, which stringify every
field value** — they are not the source shape. The source shape is settled by two independent
places in the repo: the template's `measured_from` (a real `polaris-logs-*` readout) and
`fluent-bit/values.yaml`'s own note that `Id_Key sequence` indexed 0 of 13,737 records
*because* Polaris' `sequence` is a JSON integer and the directive needs a string. Had I not
checked the provenance of the sample, I would have filed a confident correction that was itself
wrong — the same shape as the "rendered UI is a projection" lesson in the 09-03 session.

## NOT VERIFIED

No `helm lint`, no `--dry-run` render, no cluster command. The two inverted gates have had
`bash -n` only; neither has been run against a render or a cluster. YAML and JSON parse. The
tree should not be trusted as rolled until `step2` passes on a real render.

---

# Part 2 — the roll (same day, Kade at the cluster)

## I gave a wrong command and it produced 21 false failures

step2's first run came back `RESULT: 21 check(s) FAILED — do not upgrade.` Nothing was wrong
with the change. **I had added `--debug` to the render command**, combining CLAUDE.md's DoD
wording (`--dry-run=client --debug`, right for reading a manifest by eye) with step2's own
documented usage (`--dry-run=client`, no `--debug`). With `--debug`, Helm prints
`USER-SUPPLIED VALUES:`, then `COMPUTED VALUES:`, then `MANIFEST:` — and the `config.inputs/
filters/outputs` blocks appear in all three, so every `grep -c` in the gate triples.

**The tell was in the arithmetic, not in any individual check:** every failure was exactly 3× its
expected count (want 2 → 6, want 1 → 3, want 3 → 9) and every check expecting 0 passed. One
failure did not fit that pattern and confirmed the diagnosis outright: `no reloader image` wanted
0 and got **1** — that string exists only in the fluent-bit chart's *default* values, which only
`--debug` prints. Nothing in the repo references a reloader.

Worth keeping because the failure was legible only in aggregate. Read check-by-check, 21 failures
across five unrelated sections reads like a corrupted values file; read as a column of numbers it
is obviously one input defect. **When a whole gate fails, suspect its input before its subject.**

It also means step2 has a real usability hole: handed a wrong-shaped render it produces 21
confusing failures instead of one clear "you passed --debug". Offered to Kade as its own commit;
not taken up in this session.

## The roll, and what it proved

Clean render → step2 clean → `helm upgrade` → step3 twice, before and after traffic. Both
`RESULT: post-upgrade checks passed`.

**After traffic, section 5:**

```
PASS  polaris-logs-*: 367 docs carry message since pod start
PASS  polaris-logs-*: 367 docs carry threadName.keyword since pod start
PASS  polaris-logs-*: 367 docs carry threadId since pod start
PASS  polaris-logs-*: 0 docs with ndc since pod start
```

367/367, and `ndc` 0 — the exact inverse of `#30`'s "0 of 386". Every v6 absence still holds.

**Three secondary readings that each say something the primary one does not:**

- **Lua ConfigMap sha `f92bb6d4dbbfc346`, unchanged, last written 2026-09-16T15:59:12Z.** This is
  the positive proof that the roll was values-only and no `apply-lua.sh` ran — better evidence
  than "I didn't run it," because it is a property of the cluster rather than of anyone's memory.
- **Tier-2 output `ok=367 errors=0 retries_failed=0`, pod log clean.** A per-item OpenSearch
  rejection inside an HTTP 200 increments none of the counters, so the pod log is the only place
  it shows — and it is clean. **Today's index was shaped by dynamic mapping, not the template**
  (not retroactive), and `threadId` indexed fine anyway. That is empirical confirmation of the
  correction I made earlier in the day: the explicit `threadId: long` mapping is defensive, not
  load-bearing. I had argued it from the mapping rules; the cluster then demonstrated it.
- **`polaris_noise_filter dropped=497 added=164`.** 367 stored + 497 dropped = 864 in, a 57.5 %
  drop against the v5 policy's 58 %. The two fields changed what each record carries, not what
  the filter decides — which is the thing a field change could plausibly have broken.

## The gate that verified it had a hole, and it was mine

`RESULT: post-upgrade checks passed` does **not** mean the thread fields are present. step3's
`huh()` prints `????` and never increments `FAIL`; the `#42` presence checks I wrote called `huh`
on zero documents, copying the `message` idiom. **The pre-traffic run proves the hole exactly:**
`????` on all three presence checks, and `RESULT: post-upgrade checks passed`.

`#42` is verified regardless, because I asked for the `PASS` lines and read them rather than
trusting the RESULT line. But that is luck of process, not design — a future reader of that
RESULT line would have been entitled to conclude something it does not support.

Fixed as `#43`: the checks self-arm off `$M`, the count of documents carrying `message`. If
documents are being written and the fields are absent *from those documents*, that is a real
`bad`. Only when nothing has been written at all does 0 stay uninformative. The general `huh`
mechanism stays — it exists for checks that genuinely cannot tell "broken" from "not yet". The
rule that came out of it: **a presence check needs an arming signal, or it is not a check.**

Note the shape recurring three times in one day: the `.keyword` trap (a gate that would have
failed for the wrong reason), the `--debug` render (a gate that did fail for the wrong reason),
and this (a gate that passed without asserting). All three are the same failure — the gate's
verdict not tracking its subject — and only the first was caught before it cost anything.

## Open at the end of the session

- **`step12` output was never read.** If it did not run, the `threadId: long` declaration is
  still only in the repo and tomorrow's index is dynamic-mapped again. Harmless on today's
  evidence; contrary to the file's whole purpose. Expect **8/8**, was 7/7 under `#30`.
- helm revision not recorded (expect 21). `step10`/`step11` not run, so `#32`/`#31`'s
  detail-by-logger and report-row equalities were not re-established on this roll.
- `#43`'s new `bad` branch has never fired — it requires `message > 0` with the field count at 0,
  which is precisely the state this roll did not produce.
- Average document size: **deliberately not measured.** See `#42` for why the measurement was
  withdrawn rather than skipped.
