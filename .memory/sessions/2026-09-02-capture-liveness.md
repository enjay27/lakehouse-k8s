# 2026-09-02 — why three clean drives captured no SQL

## The finding

The capture tail dies when notebook `03` starts it and survives when a terminal
does. Everything downstream of that — runner, parser, streams, EXPLAIN tooling —
was already working.

Decisive numbers: seven notebook-started captures hold **25 lines** each; one
terminal-started CLI drive holds **859 lines** with the tail alive.

## The wrong turns, in order, because they are the expensive part

**Wrong turn 1 — "it is the Polaris startup burst."** The 2026-09-01 HANDOFF
read four runs at 1,311,11x bytes, concluded startup dump, and prescribed a
tracer-level preflight plus a longer `settle_s`. The byte constant is real and
the inference from it was wrong: `polaris.log` is **25 lines**, one of which is
**1,292,023 bytes** — `PolarisServiceImpl` logging `listCatalogs returning:` at
INFO. Four runs matched in size because they all die at the same place and that
place is dominated by one constant-size line. *Lesson: a suspicious constant
deserves `wc -l` before it deserves a theory.*

**Wrong turn 2 — "the oversized line kills `kubectl logs -f`."** Mine, and it
had the shape of a good hypothesis: the stream stops one line after a 1.29 MB
line, `polaris.err` is empty, the tail exits silently. Probe: start a capture,
issue one `list_catalogs`, then ten cheap calls. **Tail alive, +112 lines.**
Later confirmed twice more — the 859-line drive pushed two more oversized dumps
(548 KB → 1.88 MB → 2.46 MB) through the same tail.

**Wrong turn 3 — "the rollout leaves the tail on the terminating pod."** Also
mine, and it fit every observable: old pod still in Endpoints serves the auth,
then dies; stream ends silently; new pod serves the sweep unlogged; identical
failure every run. Probe: restart, rotate, same calls. **106 lines, tail alive.**

Three theories, three measurements, three refutations. What actually located it
was not a theory but a **split**: the only remaining difference between a healthy
run and a broken one was *what issued the calls*, so the next probe ran the real
runner from the CLI with a poller on the log. 859 lines. That halved the space in
one shot and cost one drive.

*Lesson worth keeping: after two failed hypotheses, stop hypothesising and
bisect. The probe that pays is the one whose two outcomes are both informative.*

## What was checked and cost nothing

- `capture-admin-index` / `capture-admin-noindex` (2026-08-31) hold 2,371 and
  2,170 lines. The pipeline worked before 2026-09-01 — that comparison alone
  ruled out "this never worked".
- Seven broken captures have seven distinct inodes and seven distinct contents,
  so `archive_capture`'s rename is not creating the artefact.
- `pkill|killpg|.kill()|terminate()|SIGKILL|os.kill` across `src/` and
  `diagnostics/api-sql-profile/*.py`: **no matches.** Nothing in Python kills the
  tails. The only `capture.sh stop` is at the top of cell 19, before the start.
- `capture_snapshot` / `capture_verdict` are read-only (`os.path.getsize`).

## Two defects found on the way

- `find_capture_dir()` requires a non-empty `polaris.log`, so a freshly-started
  capture is not a candidate; with 15 capture directories present it can select a
  stale one. Always pass `--capture` explicitly.
- `capture.sh do_stop` reaps by `pgrep -f "kubectl.*-n $NS.*logs.*-f"` — it kills
  other captures' tails, not only its own.

## Open, and the probe that closes it

Cell 19 starts the tails via `sh()` = `subprocess.run(shell=True,
capture_output=True)` from the Jupyter kernel. Run cell 19, run nothing else,
poll the tail PID and `polaris.log` for 60 s. Dies while idle ⇒ the fix is
detaching the tails (`setsid` / `nohup` / `start_new_session=True`).

Unblocked meanwhile: drive from the CLI, `--capture` explicit. HANDOFF §1.6.

---

# Part 2 — the actual root cause, and it was a false alarm all along

## The finding

The capture was working. **The gate was lying about it.**

Notebook 03 cell 9b read its log tail by CHARACTERS:

    _ptail = _pl.read_text(errors="replace")[-40000:]

`polaris.log` ends with a single **1,292,023-byte** line — `PolarisServiceImpl`
logging `listCatalogs returning:` at INFO with the whole catalog list inlined.
The last 40,000 characters lie entirely inside it: no line boundary, no markers,
and the file's 19 `DatasourceOperations` lines are at the *start*. The gate
counted **0**, concluded "the logger is above DEBUG, so no SQL will ever be
captured", and raised.

That message is the origin of everything: the 2026-09-01 handoff's startup-burst
theory, its wrong preflight fix, and my own three refuted hypotheses. A healthy
capture reported as a dead logger.

## What the notebook's own saved output showed, that nobody read

- **The gate did not "pass anyway".** It RAISED. The handoff's §1 said it passed,
  and a gate believed to pass spuriously is a far worse defect than one that
  failed and was overridden — the design was being bent around a fiction.
- **The drive under it SUCCEEDED**: 43/43, 39 permitted, 1 refused, 0 errors,
  `{200:22, 204:11, 201:6, 500:2, 404:1, 403:1}`, driven as
  `admin1_principal scope=PRINCIPAL_ROLE:service_admin`. The single refusal is
  `mgmt.reset_principal_credentials` — **the "admin is not a superset" finding,
  sitting unread in a saved cell output for a day.** Only the SQL capture was
  missing, never the drive.

## The lesson worth more than the fix

Four hypotheses died before this one. What killed the last three was measurement;
what killed the FIRST one should have been `wc -l`. The tell was there from the
start: four runs at 1,311,11x bytes, and the file is 25 lines. A suspicious
constant deserves a line count before it deserves a theory.

And the deeper one: **the failure was in the instrument, not the experiment.**
Three sessions treated the gate's output as data about the cluster. It was data
about a `[-40000:]` slice. When a measurement says something surprising, doubt
the measurement's window before doubting the world — especially a window sized
in bytes over text whose line lengths you do not control.

*General rule now recorded in active-issues: any window over log text is counted
in LINES, never bytes or characters. This repo's logs contain megabyte-scale
single lines.*

## Fixed

- `privilege_scan.tail_lines(path, n=800, max_line=4096)` — streams, windows by
  lines, truncates each. Markers all live in a line's first few dozen chars.
- `capture_verdict` no longer asserts "logger above DEBUG" as *the* cause; it
  names both causes and their different fixes.
- Cell 9b uses `tail_lines` for both the Polaris and the pg tails.
- Four regression tests reproducing the fault at 1/10 scale, including one that
  asserts the CHARACTER window fails — so the bug cannot come back unnoticed.
- `probe_capture_liveness.py`, the two-arm probe that exonerated `sh()`.

## Parked, deliberately

Both stream families stopped together during the 2026-09-01 drives (polaris.log
identical before and after a 43-op drive; no pg log grew). Falsified as causes:
the oversized line, a rollout orphaning the tail, `sh()`'s `capture_output`,
`settle_s`, the parser, the runner. The CLI path records correctly (859 lines),
and the corrected gate plus per-operation liveness will report it truthfully on
the next drive instead of being guessed at again.
