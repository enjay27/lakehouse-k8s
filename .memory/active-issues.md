# Active issues — index

The bulk is split by half, because merging them would make a 289 KB file:

- [`active-issues/platform.md`](active-issues/platform.md) — cluster, charts, Fluent Bit,
  OpenSearch, PostgreSQL. Numbered `#1..#47`.
- [`active-issues/catalog.md`](active-issues/catalog.md) — the suite: coverage denominators,
  harness gaps, notebook defects. 13 open, 5 resolved-but-instructive.
- [`active-issues/merge.md`](active-issues/merge.md) — what the 2026-09-21 merge deferred.

**Issue numbers are per-half and they collide.** Platform `#24` and catalog `#24` are different
issues. Until the two files are reconciled, always say which half you mean.

Headline items as of 2026-09-21 — the full entries are in the files above:

| | issue |
|---|---|
| platform | plaintext OpenSearch password in `releases/fluent-bit/values.yaml` tier 1 — documented in four places, fixed in none |
| platform | `#41` the 1.6.0 pod that crashed 3x at rollout — **perishable, still unread** |
| platform | `#46` a 5xx whose path saw no earlier success in the window lands in `__errors__`, not its resource row — counts survive, attribution does not |
| platform | `#24` malformed-request 500s reproduce on 1.6.0 (all NPEs) — `errors_5xx` is not a health signal on its own |
| catalog | the fixture catalog will not drop; `delete catalog` 400 "cannot be dropped, it is not empty" |
| catalog | `api_report.py:307` hardcodes the pre-1.6.0 version |
| catalog | `03_api_index_matrix` carries a literal `clientSecret` in `HEAD` |
| catalog | nothing checks a request without driving it — `--spec-check` was removed 2026-09-10 |
| merge | notebook `sys.path` bootstrap depth is wrong after the move |
| merge | absolute `$HOME/hynix/local-k8s/...` paths in three files |
