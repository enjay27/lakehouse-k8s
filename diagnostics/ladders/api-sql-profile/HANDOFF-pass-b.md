# HANDOFF — the confound first, then Pass B (latency)

Written 2026-08-31, after the index contrast was read
(`doc-grant-index-contrast-20260831.md`). Standalone.

Supersedes `HANDOFF-index-contrast.md`, whose task is complete: its §4 sweep
ran, its §6 definition of done is met, and its §5 git guard is resolved (Claude
auto-commits now — see CLAUDE.md *Version Control*).

---

## 0. Where this stands in one paragraph

The **shape** question is answered and reported: without
`idx_grant_records_grantee` the grantee lookup Seq-Scans 572 pages to discard
60,783 rows and return 1; with it, an Index Scan of 3 pages discarding none.
Identical across three fixtures, control in the same table, 29 of 29 read
operations affected. That result needs no clock and is not in doubt.

The **latency** question — what the index is worth in milliseconds — is
untouched. Every pass so far ran with statement logging ON (measured 4.6x
inflation), so all six clocks were discarded by design. Pass B is that
measurement, with logging off.

**Pass B is not yet safe to run.** The banked data contains an unexplained
asymmetry that would ride along inside any naive A/B latency number, and step 1
below is the cheap offline test that settles it. Do that first.

---

## 1. THE BLOCKER — the index-absent passes issued MORE statements

Not just slower ones. On the `user` tier:

| pass | statements | `GET  /namespaces` per request |
|---|---:|---:|
| index absent (`privscan-...-110305`, ran first) | 122,010 | 13.5 |
| index present (`privscan-...-111114`, ran second) | 109,010 | 8.0 |

An index changes how a statement executes, never how many are issued. So this
is something else. The standing hypothesis is **Polaris `InMemoryEntityCache`
warmth** — the absent passes ran first, against a colder cache — but it is
recorded as *unexplained*, not attributed, and must stay that way until
measured.

**Why this blocks Pass B.** The two halves ran in a fixed order: absent first,
present second. If cache warmth is real, a Pass B run in the same order
measures `index effect + warmth` and reports the sum as the index effect. That
is precisely the class of error this audit has already caught three times (the
02c noise floor, the 4.6x logging inflation, the root-vs-user identity).
Running Pass B before settling this would produce a number nobody may quote.

### 1.1 The test — offline, free, no cluster, no drives

Both raw captures are on disk and hold per-request timestamps and principals:

```
capture-user-noindex-2/   274M   polaris.log + pg-0.log
capture-user-index/       257M
```

`query_profile.correlate()` returns `RequestProfile` objects carrying
`.timestamp`, `.principal`, `.label` and `.statements`. So:

**Bucket each pass's `GET  /namespaces` requests by position within its own
pass** — by identity index parsed from `.principal` (`user{N}_principal`), or by
`.timestamp` into deciles — and read the per-request statement count across the
bucket sequence.

- **Decay within a pass** (early identities dear, later ones cheap, both halves
  converging on the same floor) is the cache-warmth signature. Hypothesis
  confirmed; the fix is a warm-up, see §2.
- **Flat within each pass, but at two different levels** refutes cache warmth.
  Something structural differs between the two drives and must be found before
  either half is trusted for anything — including, retroactively, the statement
  counts already published. The report's "not comparable across halves" caveat
  would become a finding.

Localise it too: is the excess confined to `GET  /namespaces`, or is that just
where it is largest? Which statement shapes carry the extra ~13,000?

Write it as a script beside the others — `analyse_cache_warmth.py` — not as a
notebook, and have it emit `runs/warmth-<ts>.json` so the answer is a file
rather than a screenful.

**Guard:** `GET  /namespaces` also carries the `[ns-resolve]` harness label,
which folds onto the base op. Confirm the fold is not itself the asymmetry
before concluding anything about Polaris — a harness that resolved the
namespace more often in one pass than the other would produce exactly this
signature and say nothing about caching.

---

## 2. PASS B — the design the answer to §1 selects

Logging OFF (`./capture.sh pgoff`; note `rotate` is `do_stop; do_start` and does
**not** touch `log_statement` — that mistake cost a whole 9,000-request pass on
2026-08-24). No statement capture, so no correlation: Pass B measures
wall-clock per operation and nothing else.

Whatever §1 concludes, Pass B does **not** repeat the fixed absent→present
order. Two changes, both cheap:

1. **A discard warm-up drive before every measured drive**, so each half is
   measured against a warm entity cache. `SWEEP_WARMUP` in 02c was raised 2→10
   for the same class of reason (ZGC JVM outliers) — the precedent exists.
2. **Order-balanced halves** — present / absent / absent / present, or two
   independent A/B pairs. If the two measurements of the same index state
   disagree by more than the within-state spread, the order effect is bigger
   than the index effect, and the run must say so instead of reporting a delta.

Report the **within-state spread as the noise floor** and refuse to quote any
delta smaller than it. That is `noise_floor()`'s existing lesson from the 02c
smoke run: the floor is the within-cell min/max spread, not the cross-cell one.

**State the index state from live `pg_indexes` at drive time**, as
`profile_queries.py --index-state` already does. A latency number labelled with
a cluster state nobody checked is the same fault that flag was built to prevent.

---

## 3. Cheap wins to fold in — read-only, and they close named holes

- **`admin`'s grant footprint has never been measured.** The report and both
  handoffs say "~1,100, assumed from `service_admin`'s one-grant-per-catalog
  property". One command settles it:
  `python3 scan_privileges.py --footprint --profile service-admin`.
  Until then it stays labelled *assumed* everywhere it appears.
- **The four `NO_PARAMS` write statements** (an `entities` UPDATE + three
  DELETE/INSERT variants; placeholder count spans SET/VALUES). Predicates are
  PK-shaped and *likely* fine — but unmeasured, and must not be called verified.
  `capture_write_templates.py` exists for this.

---

## 4. What you cannot do from the Claude session

Measured 2026-08-31: the device VM Claude's shell runs in has **no `kubectl`,
no `psql`, and no route to the cluster** (`127.0.0.1:8181` connection-refused).
PyPI *is* reachable, so `black` / `isort` / `pytest` run fine there — the
earlier note claiming otherwise was wrong, and the pytest shim it forced is
unnecessary.

| step | who |
|---|---|
| §1 the warmth analysis (offline, banked captures) | **Claude** — no cluster needed |
| §3 the footprint / write-template reads | Kade's shell (needs the cluster) |
| §2 Pass B drives + index toggles | Kade's shell |
| analysis, report, tests, commits | **Claude** |

---

## 5. Guards carried forward — every one a scar

- **Check content before trusting a document about content.** The previous
  handoff said nothing had been EXPLAINed; six `qprofile-*.json` with full plans
  were already on disk. Acting on the document would have re-run the sweep and
  toggled the index twice for data that existed. This repo already applies that
  rule to capture directories. It applies to its own handoffs.
- **A prepared fix nobody finished is indistinguishable from no fix.** The
  full-surface sentinels sat in `_SENTINELS` with a comment saying what they
  were for, while the default stayed frozen at 13 ops through six captures.
- **Errors that net out survive reconciliation.** 75 missing from template rows,
  77 arriving on raw-path rows, sum +2 — a normal-looking total on all six
  captures. Read per-row composition, not the summary line.
- **A banner that cries wolf trains you to skip it.** All six reconciled at +2
  and printed "is not what the drive issued" because the liveness probe is not
  in the run manifest. Now named, capped at the probe's own cost.
- **EXPLAIN replays against the CURRENT database**, not the one the capture came
  from. `--index-state` is required with `--explain` and checked against live
  `pg_indexes`.
- **`ANALYZE` after every index toggle.** A planner on stale `reltuples` picks a
  path for a table size that no longer exists.
- **`capture.sh rotate` does not enable statement logging.** `pgon` is separate.
- **`privscan-20260831-105120` is a SUPERSEDED authz no-index run.** The live
  pairings are in `doc-grant-index-contrast-20260831.md` §1.
- **The clock from every Pass A capture is discarded.** Logging on, 4.6x
  inflation measured. The elapsed drops (−41% / −29% / −35%) are a hint for
  Pass B to confirm, never a result.

---

## 6. Definition of done

- `runs/warmth-<ts>.json` + a written answer: cache warmth confirmed or refuted,
  with the within-pass curve that settles it, and the excess localised to
  statement shapes.
- If confirmed: Pass B run warm and order-balanced, with the within-state spread
  reported as the noise floor.
- If refuted: the structural difference named, and the report's "not comparable
  across halves" caveat upgraded from caveat to finding.
- `admin`'s footprint measured, or still explicitly labelled *assumed*.
- `black` (last) and `isort` clean, `pytest` green.
- `MEMORY.md` *Now* updated; `.memory/roadmap.md` and `.memory/sessions/`
  written.
- Committed — automatically, one commit for the task, subject stating the
  finding.
