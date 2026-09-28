# Active State — lakehouse-k8s

**Index, not the record.** Only what would be *false* the moment it goes stale lives here.

## Now — 2026-09-29 (repo cleanup on branch `refactor/2026-09-29-cleanup`, not merged, not pushed)

**Cleanup done:** VictoriaLogs code gone, 55 finished docs deleted (index + recovery:
[`docs/DELETED-2026-09-29.md`](docs/DELETED-2026-09-29.md); before-state on `archive/pre-cleanup-2026-09-29`),
memory tree merged. It surfaced four things ([session](.memory/sessions/2026-09-29-repo-cleanup.md)):
**`apply-lua.sh` was broken since the merge, fixed** (`#52`); **`helm upgrade` of `charts/minio` would
bring MinIO up EMPTY** (`#53`, do not upgrade it before reading); **Fluent Bit dropped 2 chunks to
OpenSearch on 09-27** (`#49`); matrix reports since 09-18 carry "Polaris 1.3.0" in their header (fixed forward).

**Log batch** (`logging/HANDOFF-polaris-log-batch-2026-09-28.md`): **LIVE since 2026-09-29** — release
`polaris-log-batch`, hourly at HH:03 KST, limit 2Gi (rehearsal peaked 838 MB). First run published 27 hours,
matched the local rehearsal on every count, moved 14 orphans ([session](.memory/sessions/2026-09-29-polaris-log-batch-first-run.md)).
Next: Lua parity on real traffic, parallel run vs Fluent Bit tiers 2/3.

**Lua pipeline:** `WINDOW_SECONDS` target **3600** (decided 2026-09-21) is **not rolled**; live is still the
verification 30 (`logging/HANDOFF-pipeline-next-2026-09-16.md`). Roll with `bash releases/fluent-bit/apply-lua.sh`.

**Suite:** pytest **1069 passed**; a clone needs `fetch_specs.sh` first. Run `1789955605`: **+8 on the
shared 286-cell subset** (quote the +8, not raw 245/297). The fixture catalog still will not drop.
**NEEDS KADE:** export `POLARIS_WATCHDOG_CLIENT_ID` / `_SECRET` for the availability notebook; rotate the
principal whose secret is committed in `03_api_index_matrix` output.

**Secrets committed and unfixed:** OpenSearch password in `releases/fluent-bit/values.yaml` (`#4`),
DB password in the live release (`#9`), the notebook above. `#41` (1.6.0 crash) is perishable, still unread.

**Standing.** Polaris is not to be changed. Verify against the running object. Record denominator fingerprints.

## Where the detail is

| read | when |
|---|---|
| [`.memory/README.md`](.memory/README.md) | which memory file takes what |
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** |
| [`.memory/active-issues/`](.memory/active-issues/) | before trusting a value, a number or a runbook |
| [`logging/README.md`](logging/README.md) | which `logging/` document is current |
| [`docs/DELETED-2026-09-29.md`](docs/DELETED-2026-09-29.md) | a path some older note names that no longer exists |
