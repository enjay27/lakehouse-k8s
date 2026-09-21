# Active State — lakehouse-k8s

**Index, not the record.** Only what would be *false* the moment it goes stale lives here.

## Now — 2026-09-21 (the merge: two repos became one, nothing deployed changed)

**`local-k8s` and `polaris-learning` are one repo as of today.** 554 files at HEAD relocated;
both pre-merge histories are here on their own refs (`git log archive/local-k8s`,
`archive/polaris-learning`; `git log --all --grep=` searches both). Why and the full path
mapping: [`docs/MERGE-2026-09-21.md`](docs/MERGE-2026-09-21.md).

**The suite gate is green — `pytest` 996 passed, 0 failed**, after repairing the 20 of 21 test
modules the move into `tests/` broke
([session](.memory/sessions/2026-09-21-merge-test-repair.md)). **A clone still needs
`fetch_specs.sh` first**, or 13 fail and 49 error on `SpecUnavailable`. **The platform gate has
never run** — no `helm`, no `kubectl` from here — so charts, values and templates stay unverified.
Open seams: M1 notebook bootstraps (**61 notebooks, not 66; the 5 in `diagnostics/` must not be
touched**), M2, M3, M4/M5, M6, M10 —
[`.memory/active-issues/merge.md`](.memory/active-issues/merge.md).

**Platform.** `WINDOW_SECONDS` has a decided target of **3600, one hour** (Kade's manager,
2026-09-21), replacing the 1800 older documents call "the revert" — **written, not rolled**; it is
a Lua change (`releases/fluent-bit/apply-lua.sh`) and the running value is still the verification
30. Retunable during monitoring, so read `window_seconds` off a report row. After the roll check
the per-window caps, not index size. The **plaintext OpenSearch password in
`releases/fluent-bit/values.yaml`** is documented in four places and fixed in none. `#41` (the
1.6.0 pod that crashed 3x at rollout) is **perishable and still unread**.

**Suite.** **POLARIS IS 1.6.0**; `api_report.py:307` still hardcodes the old version. Run
`1789955605` measured session 17's fixes: **+8 on the shared 286-cell subset** (231 -> 239) —
**quote the +8, not the raw 245/297**, the denominators differ. The **fixture catalog still will
not drop**; the suspect is `createNamespace`'s 400 cell returning 500 with a null namespace, and
the next drive resolves it. **NEEDS KADE:** the availability credential (deliberately uncommitted,
**not carried into this repo**); `04_explain_sweep.ipynb`'s `latest_report()` returns `hits[-2]`;
`03_api_index_matrix` has a literal `clientSecret` in `HEAD`. Fast-run settings (30/5) are
**temporary** — revert together.

**Standing.** Polaris is not to be changed. **Verify against the running object, never an intent
artifact.** A figure whose denominator fingerprint is unrecorded is not reproducible.

## Where the detail is

| read | when |
|---|---|
| [`.memory/README.md`](.memory/README.md) | which memory file takes what |
| `.memory/environments-{platform,catalog}.md` | **before running anything** |
| [`.memory/active-issues/`](.memory/active-issues/) | before trusting a value, a number or a runbook |
| [`.memory/roadmap/`](.memory/roadmap/) | what is next, and the verification assertions |
| [`.memory/sessions/`](.memory/sessions/) | why a decision was made, including the wrong turns |
| [`docs/MERGE-2026-09-21.md`](docs/MERGE-2026-09-21.md) | what moved where, and what was dropped |
| `logging/README.md` | which `logging/` document is current |

## Rules
- **Under ~40 lines.** *Now* carries what is next and what is written but not running; nothing
  else. A paragraph summarising a file that exists does not belong here.
- **Update *Now* every session**, even when the answer is "unchanged".
- A fact with a number goes in `.memory/roadmap/`; the story goes in `.memory/sessions/`.
  Configuration written but not applied goes in `.memory/active-issues/`.
