# Roadmap — index

Split by half; see [`../MEMORY.md`](../MEMORY.md) for what is live right now.

- [`roadmap/platform.md`](roadmap/platform.md) — cluster milestones, the pipeline verification
  numbers, and the PostgreSQL verification assertions to run after any PostgreSQL change.
- [`roadmap/catalog.md`](roadmap/catalog.md) — coverage runs, denominators, gate results.

**Quoting a number from either file: check its denominator first.** The coverage denominator
moved from 63 operations / 286 cells to 65 / 297 when the 1.6.0 documents were vendored on
2026-09-21, which left run `1789950539`'s `231/286` unreproducible because nothing recorded the
fingerprint it replaced. `assert_denominator` now hard-fails on drift. Re-record deliberately, in
a commit that says why — never to turn a red run green.
