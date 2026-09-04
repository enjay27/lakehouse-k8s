# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-04 (run 1)

**Read [`log-coverage/PLAN-log-coverage.md`](log-coverage/PLAN-log-coverage.md) first — standalone.**

**THE RETENTION POLICY HAS NEVER BEEN DEPLOYED, and the notebook's first run proved it.**
Nothing is dropped: 20 identical table GETs → **20 stored**, three successful OAuth token
requests → **3 stored**, every `create_principal` / rename / credential reset → **stored**.
0 of 34 expected drops actually dropped. `logging/fb-values.yaml` gained `polaris_noise_filter`
in `local-k8s` commit **2120ed9 at 08:26:18Z on 2026-09-03**; the shipper pod has been up since
**08:04:06Z**, from **60b94d9**, which carries the access-log parser and no noise filter. Parsed
fields present, zero drops — exactly what was measured. `helm upgrade` was never run.
**This is the repo's signature failure — written is not live — caught empirically.**

Settled by the same run: **`Polaris-Request-Id` IS honoured** end to end, so correlation is
EXACT (one `list_catalogs` → **15 records** sharing the id: its access-log line plus 14 DEBUG
SQL lines). Client-side latency, the only source there is with no `%D`: median ~18 ms, and
`mgmt.reset_principal_credentials` → **403** as root, the "admin is not a superset" finding
again. **8 ERROR records, none carrying an `exception` object** — pending the raw-file check.

**Fixed after the run, all mine:** the replay dedup keyed on `mdc.requestId`, which collapsed
2,049 records to 122 and capped every `stored` at 1 — it now keys on `(hostName, sequence)`;
the 403 case used a client that was never tagged, so its record was invisible; the
`http_status` type check was meaningless (VictoriaLogs returns every field as a string) and now
runs a real numeric LogsQL filter; the `events` lookup searched `public` instead of
`POLARIS_SCHEMA`. Cell 0 now **aborts** when the ConfigMap does not carry the policy. 117 tests
green under the stand-in runner; **`pytest`/`black`/`isort` still not runnable from Cowork.**

**Next:** `helm upgrade` the shipper in `local-k8s`, then re-run. Until then no number in
`doc-log-coverage-results.md` describes the intended pipeline.

## Where the detail is

| read | when |
|---|---|
| [`.memory/roadmap.md`](.memory/roadmap.md) | what is done, what is next |
| [`.memory/active-issues.md`](.memory/active-issues.md) | before trusting a number or a tool (13 open, 5 resolved-but-instructive) |
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** — local / dev / prod, and what must never run where |
| [`.memory/repository-map.md`](.memory/repository-map.md) | looking for where something lives |
| [`.memory/goal.md`](.memory/goal.md) | the standing objective and structural model |
| [`.memory/sessions/`](.memory/sessions/) | why a decision was made, including the wrong turns |
| [`.memory/completed.md`](.memory/completed.md) | finished structural work |

Task-specific handoffs live beside the code they describe, in
`diagnostics/api-sql-profile/HANDOFF-*.md`. They are written for someone
starting cold and are the right first read for a task; this file is the right
first read for the *project*.

## Rules for keeping this file useful

- **This file stays under ~40 lines.** Growth belongs in `.memory/`, not here.
  It was 198 lines against its own 150-line limit once, and a tracking document
  nobody finishes reading tracks nothing.
- **Update *Now* every session**, even when the answer is "unchanged".
- **A finding with a number goes in `.memory/roadmap.md`; the story goes in
  `.memory/sessions/`.** The wrong turns do not survive summarising and are the
  part most likely to be repeated.
