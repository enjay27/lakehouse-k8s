# 2026-09-21 — Fluent Bit documentation realigned, and the 09-21 traffic reviewed

Cowork session, no cluster reach. Kade asked for the Fluent Bit docs to be brought up to date, then
handed over two OpenSearch exports from a run whose traffic logic he had changed, and asked for those to
be reviewed first.

## The review came first, and it changed the docs work

The exports were `polaris-logs-2026.09.21` (391 docs) and `polaris-report-2026.09.21` (122 rows), copied
out of the Dev Tools response panel — so `"""`-quoted and not valid JSON. `logging/scripts/devtools-json-fix.py`
already exists for exactly this; I wrote the same conversion inline before noticing it, which is the
first small waste of the session.

All seven invariants pass (numbers in `roadmap.md`). One apparent failure was mine: I checked
`summary.bytes_total` against a sum of `bytes_total` over resource rows, got two mismatched windows, and
was about to report it. Resource rows carry **`response_bytes`**; with the right field the margin is
exact. `SCHEMA-report.md` invites that error — it says `bytes_total` is "summed over resources only"
without saying the resource rows spell it differently. Noted, not yet fixed.

What the changed traffic actually added, none of which existed in the 09-16 data:

- a **black-hole catalog** (`nb1789965827bh`, S3 endpoint `127.0.0.1:1`) producing 500s on demand. Those
  three landed in `__errors__`, not on their resource row — `#46`. By design, but the design was only
  written down in a Lua comment.
- `#24`'s four malformed-request 500s, **reproduced on 1.6.0** — all four, all NPEs.
- a `PolarisEventListeners` ERROR, new in 1.6.0, kept by rule 1 rather than the allowlist — `#45`.
- `LocalIcebergCatalog` dropping 42 lines in 25 s, which trips the Lua's own APP_ALLOW review condition.

## Then the documents

Four commits, in this order, because each is a different kind of change:

1. **Archive.** `logging/` held 30 files, sixteen of them finished. Moved to `logging/archive/`, renamed
   `YYYY-MM-DD-<name>` by creation date. Kade's call: outdated docs get their own directory, dated.
2. **`PROPOSAL-polaris-audit-log-retention.ko.md` → `SPEC-polaris-audit-logging.ko.md`**, with its status
   claims corrected (thread fields, ISM live, pod name, window still 30 s, Polaris 1.6.0 absent from 974
   lines) and three new §11 entries.
3. **The sample guide is now generated.** `step14-sample-doc.py` + `GUIDE-sample-data-2026-09-21.ko.md`;
   the 09-16 edition archived with a banner.
4. **Fluent Bit docs + memory tree**, this commit.

## Two things I decided not to do, and why

**The Lua keeps a stale link.** The relink pass rewrote a comment in
`fluent-bit/polaris_access_log.lua` that cites the moved allowlist plan. That file *is* the ConfigMap:
changing a comment changes its sha, `apply-lua.sh` sees a diff, and the pod restarts — resetting every
window counter, `report_seq` to 1, dropping held lines. Reverted and verified byte-identical to HEAD
(`d1a6439`). A documentation rename does not get to cost a rollout. `archive/README.md` carries the
redirect instead.

**`.memory/sessions/*` were not relinked.** A session record describes the repo as it stood on its date.

Also not moved: `logging/fb-values.yaml` and `victoria-values.yaml`. Both are dead configuration and both
belong in the archive by the letter of the rule, but they are cited by ~30 files, mostly session records
that must not be rewritten. Left in place, bannered, with the reason recorded in `archive/README.md`.

## The wrong turn worth remembering

`git checkout -- <file>` **cannot revert a file in this mount**: git reverts by unlink-and-recreate and
deletion is not permitted, so it fails with `unable to unlink` and **leaves the file modified while
`git status` briefly reports it clean**. I nearly took that as success. The way back is to rewrite the
content in place (a python read-modify-write) and then compare `git hash-object` against
`git rev-parse HEAD:<path>`. Every git call also left `index.lock` / `HEAD.lock` / `objects/*/tmp_obj_*`
behind; those were moved to `.git/_to_delete/` after each one, per CLAUDE.md.

## Open after this session

- `WINDOW_SECONDS` is still 30, now five days old, and the cost is measured: 28 of 30 summary rows empty.
- The plaintext tier-1 OpenSearch password in `fluent-bit/values.yaml` (`#4`, SPEC §11-15) — documented
  in three more places this session, fixed in none. It needs a Secret and a permission check, not a doc edit.
- `APP_ALLOW` review for `LocalIcebergCatalog` (`#45`).
- `SCHEMA-report.md`'s `bytes_total` / `response_bytes` naming trap.
