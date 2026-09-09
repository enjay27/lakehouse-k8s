# 2026-09-09 — the pre-run baseline: the instrument works, the measurement is still missing

**Status: §3 of `logging/HANDOFF-notebook-run-2026-09-09.md` is NOT answered.** The notebook
was not run. What was run is `step4-report-readout.sh` against an idle cluster, which is the
baseline, and the handoff says in as many words what that is worth: `0 == 0` proves nothing.

## What the readout actually returned

- `polaris-report-2026.09.09` — **56 docs**. `polaris-logs-*` **does not appear in
  `_cat/indices/polaris-*` at all**, so it has still never received a single document. That is
  a different fact from "empty for the last 10 minutes" and it is consistent with idle.
- OpenSearch side (stdout-sourced): **30 summary rows, `access_seen` 0 in every one**,
  windows `04:52:30Z`–`04:57:00Z`. All 30 of the most recent report docs are summaries —
  no table or principal rows exist, which is itself what an idle window looks like.
- VictoriaLogs side (file-sourced): `access_seen` 0 in every window returned.
- Polaris: **1 replica**, `benchmarks-polaris-585587454b-nhzdr`, 0 restarts, up 5d22h.
  `fb-polaris-shipper` up 2d, 0 restarts. Neither pod moved, so no dedup or window state
  was disturbed.

## What this DID establish, and it is not nothing

The open question in §3 was never only "are the numbers equal" — it was "can this comparison
be taken at all". It can:

1. **Both report streams are alive and arriving**, at two different sinks, through two
   different credentials and two different output plugins.
2. **The grids align empirically.** The two sides share `window_start` values exactly on the
   30s boundary — `04:53:00Z`, `04:53:30Z`, `04:54:00Z`, `04:54:30Z`, `04:55:00Z`,
   `04:56:30Z`, `04:57:00Z`. This was predicted statically (both Lua carry
   `WINDOW_SECONDS = 30` and `idx = floor(now / WINDOW_SECONDS)`, a wall-clock grid rather
   than a per-process one) and is now confirmed against live data. Had the shipper still been
   at 1800s, "equal `access_seen` for one window" would have been uncomparable.
3. **The readout tooling is sound end to end** — connectivity, credentials, the
   `report_type: "summary"` discriminator, every field name it reads, and the `@timestamp`
   sort key (tier 3 runs `Logstash_Format On` with no `Time_Key`, so the plugin supplies
   `@timestamp` itself; a sort on an unmapped field would have returned zero hits and sent
   the reader back to step 3 for nothing).

So the only missing ingredient for §3 is **traffic**. The notebook is still the traffic.

## The defect this baseline exposed — an unordered query printed as if ordered

The VictoriaLogs comparison ran `| fields ... ` with **no `sort` pipe** and then `tail -8`.
LogsQL does not guarantee row order. So `tail -8` was taking **8 arbitrary rows out of ~60**
in the 30-minute range and printing them beneath an OpenSearch block that genuinely is sorted
desc. In this run the returned set skipped `04:55:30Z` and `04:56:00Z` while the OpenSearch
side had both — which reads as a shipper gap and is not evidence of one.

**At zero traffic the two sides agreed anyway, so the defect could not show itself.** With
traffic it would have lined up unrelated windows and reported the difference as a stdout
coverage gap — the exact §7 failure mode: a plausible wrong number instead of an error.

Fixed in `logging/scripts/step4-report-readout.sh`: the query now carries
`| sort by (window_start) desc | limit 12`, and `tail -8` became `head -12`.
**Match rows by `window_start`, never by position.**

Note this is NOT the known sleep-gap from `roadmap.md` ("a gap in the report stream is usually
the OrbStack VM suspending"). A suspend takes the whole node, and both releases run on it —
the OpenSearch side had the two windows the VictoriaLogs side lacked. An asymmetric gap cannot
be a suspend. It is most likely the ordering artifact above; it must be re-checked once the
query is deterministic, before it is called anything.

## Also observed — the HPA cannot currently scale (bears on guard #5 of the handoff)

`horizontalpodautoscaler/benchmarks-polaris` reports `cpu: <unknown>/80%,
memory: <unknown>/80%` with `REPLICAS 1`, age 21d. An HPA with no metrics **cannot scale**,
so `#8`'s three-pods-one-log-file hazard cannot fire during the notebook run and the
"record the replica count before and after" guard is, for this run, satisfied in advance.

Do not read that as reassurance: it means the autoscaler has been inert for as long as
metrics have been missing, and #8 stays OPEN. See `active-issues.md` #8.

## Still open, unchanged

- §3's measurement. Run the notebook, then re-run the readout **while both sinks hold the
  windows**, and do not uninstall `fb-polaris-shipper` before that number exists.
- The 30s window revert to 1800/30 is still the cutover's last step and final gate.

NOT VERIFIED from this session: no `helm lint`, no `--dry-run`, no cluster reach. The readout
output above was produced by Kade on the host and pasted in; every claim about the cluster is
his output read back, not a check this session ran.
