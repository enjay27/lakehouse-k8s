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
