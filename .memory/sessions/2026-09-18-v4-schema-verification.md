# 2026-09-18 — the v4 schema checks ran, and the PASS was narrower than it read

Cowork session. **No cluster, Docker or psql reach** (CLAUDE.md). Kade ran every command that
touched the image or the repo's `/tmp`; this session read the output, found a gap in what it
proved, and edited files.

## What Kade brought in

The verifier, run with the **shipped** v3 as its baseline:

```
v3 10   v4 21   migration 11
declared version -- v3 3, v4 4, migration 4
shared objects: 10, of which differing: 0
objects v4 adds over v3: 11
PASS
```

Then, on request, two more commands: the step 2c baseline `diff`, and a grep of the shipped v4
for every statement the verifier does not inspect.

## Three results

1. **The baseline claim is true, and had never been tested.** `CLAUDE.md` has called
   `postgresql/schema/schema_v3.sql` "the ASF-shipped file and the authority" since August.
   Diffed against `/tmp/schema-v3.shipped.sql`: **indentation only** (the repo copy is
   IDE-reformatted with deep column alignment), plus a missing trailing newline. No column,
   type, constraint, index or version value differs. So the whole delta analysis — computed
   against that file — was standing on solid ground after all.
2. **The transcription is faithful.** 11 added objects, 11 in our script, no extras, 10 shared
   objects identical. `ce72bde`'s circularity is closed: additive-only is now measured against
   the distribution, not against our own copy of it.
3. **The PASS covered less than it claimed, and the gap was occupied.** Both claims only match
   `CREATE TABLE/INDEX/SCHEMA/VIEW`. Running the verifier's own parser over the repo's v3
   showed **26 of 36 statements are none of those**. The grep of shipped v4 found two
   `COMMENT ON TABLE` statements our migration omitted — lines 226 and 295, on
   `scan_metrics_report` and `commit_metrics_report`. It also found, reassuringly, **no**
   `CREATE FUNCTION`/`SEQUENCE`/`TYPE`/`TRIGGER`, **no** `GRANT`, **no** `ALTER`, and one
   `INSERT` (the version row) — additive-only survives the wider look.

## What changed

- `postgresql/schema/migrate_v3_to_v4.sql` — the two `COMMENT ON TABLE` statements, verbatim,
  inside the existing transaction, before the version write. Upstream comments only those two
  tables; `idempotency_records` has none, and matching the shipped file beats being tidy.
- `postgresql/schema/verify_v4_transcription.py` — **CLAIM 3**. Every statement the object
  claims cannot see is compared too: a v4-added function, grant, alter or seed insert the
  migration omits now FAILS; an omitted `COMMENT ON` is a NOTE, since the database ends up
  functionally identical. Excluded as legitimately delta-vs-full-schema differences: the
  transaction wrapper, `SET search_path`, psql meta-commands, our `DO` guard, and the version
  row write (already covered by `declared_version`).
- Its header and the runbook's step 2c — the PASS, the diff result, and what the PASS does not
  mean. The migration's `PROVENANCE` block had survived `eddeea5` still telling the reader to
  run `kubectl exec deploy/benchmarks-polaris -- unzip -p /deployments/*.jar`: the command that
  hung, against a 1.3.0 pod that does not ship `schema-v4.sql`, on a path a Quarkus thin jar
  does not use. The runbook was corrected that day and the SQL file was not.
- `MEMORY.md` — the *Now* section had grown to 68 lines against its own ~40-line rule, and the
  Polaris paragraph was a 23-line digest of findings already filed in `active-issues.md`, which
  is the exact thing the file's rules forbid. Condensed to 7 lines of links and the facts that
  would be *false* if stale. 68 → 56. Every fact removed was grepped for in `.memory/` and the
  runbook first; none was only here. It also carried a live contradiction — "Step 1 reframed:
  never a blocker" and, four lines later, "1.6.0 rejects entity names … screen first" — dropped.

## Self-test, because the repo's own standard demands one

A verifier's new check is not evidence until it has failed on a known-bad input. Built a
synthetic v4 (repo v3, version bumped, plus the migration's 11 objects via the verifier's own
parser, plus the two comments):

- round trip against the migration **as committed** → PASS with exactly the two NOTEs, which
  reproduces what Kade's real run would print. After the fix: PASS, no notes.
- synthetic v4 + `CREATE OR REPLACE FUNCTION` → **CLAIM 3 trips**.
- synthetic v4 + `GRANT SELECT` → **CLAIM 3 trips**.

First attempt at building the synthetic file split the migration on `;` and got 8 CREATEs
instead of 11 — comment banners preceding a statement defeat a `^\s*CREATE` match, and the `DO`
block's inner semicolons fragment it. Used `split_statements` + `OBJ` from the module under
test instead. Worth noting the circularity that leaves: the round trip exercises the claim
logic, not the parser, since the same parser builds the input.

## Decided: do not vendor the shipped files

Proposed committing `schema-v3.shipped.sql` and `schema-v4.shipped.sql` into
`postgresql/schema/` to end their perishability. Withdrawn once the diff came back clean:
`schema_v3.sql` *is* the shipped v3, so the repo gains a duplicate and no authority, and this
repo's duplicate-file problem is already in `repository-map.md`. The v4 file is three commands
from the image.

## Open, unchanged by this session

**`2b`, the metastore dump, has not been run**, and it is the rollback for step 2 — the next
thing to do. Re-confirm pg-1 is the primary before `2e`. The HPA may undo `2d`'s scale-to-0
(`#8`).

NOT VERIFIED: no cluster, Docker or psql command was run from this session. The verifier was
re-run here only against synthetic inputs; the run against the real shipped files was Kade's,
before these edits, and it should be repeated after them if the files are still in `/tmp`.

## Later the same day — step 2 ran

Kade ran all of step 2. `2f` returned `version | 4` and nine tables in `polaris_schema`: the
six from v3 plus `idempotency_records`, `scan_metrics_report`, `commit_metrics_report`.

Two observations about that readback, recorded because the first is a design feature worth
reusing and the second is a hole in the step as written:

* **The `4` implies the indexes.** The migration is one transaction and the version write is
  its last statement before `COMMIT`, so a `version_value` of 4 means everything ahead of it
  committed — the 8 indexes included. That ordering was deliberate (it was written so a failure
  leaves the row at 3) and it pays off twice: as a rollback property and as a proof obligation
  discharged for free.
* **`\dt` lists tables only.** Step 2f asked for `\dt polaris_schema.*` and called it
  verification, so the 8 indexes were never actually listed, and neither were the two table
  comments `935c7ed` added. The inference above covers the indexes; the comments depend on
  *which* script ran, since step 2c deliberately sanctioned both ours and the shipped file, and
  ours only acquired the comments in `935c7ed`. Added a `pg_indexes` + `obj_description` query
  to the runbook that settles both, plus the two standalone `COMMENT ON` statements to apply if
  they are missing — re-running the migration is not an option, the guard now refuses v4, which
  is correct.

**New open issue `#35`: the metastore is v4 and the server is still 1.3.0.** Additive-only
means nothing 1.3.0 reads has moved, so this is not expected to bite; whether 1.3.0 *asserts*
`version_value = 3` at bootstrap is undocumented. Upstream's relational-JDBC page covers only
the reverse direction (a newer server finding an older schema, the v5 placeholder case).
Because `2d` scaled to 0, the current pod state answers it for free — and step 4 destroys the
reading, so it is perishable in the same way step 0's captures were. Direction is forward.

NOT VERIFIED: this session ran no cluster command. The step 2 output above is Kade's.
