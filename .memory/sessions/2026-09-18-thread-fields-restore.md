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
