# `releases/fluent-bit/` — what is deployed

Five files. Together they are the **only** log pipeline in this cluster: one DaemonSet release,
`benchmarks-fluent-bit` (chart `fluent-bit-0.57.6`, image `5.1.1`, namespace `datahub-hynix`), tailing
`/var/log/containers/*.log` into OpenSearch in three tiers. The second pipeline that used to exist
(`fb-polaris-shipper` → VictoriaLogs, off a shared log PVC) was uninstalled on 2026-09-18 along with the
PVC; `logging/fb-values.yaml` is its values file and is history, not configuration.

| file | what it is |
|---|---|
| `values.yaml` | the Helm values for the DaemonSet. Its header comment is the tier map, the install/upgrade sequence and the traps. **Read that header before changing anything here** |
| `polaris_access_log.lua` | the whole Polaris policy — one filter function: parses access lines, decides keep/count/drop, aggregates the window, emits the report. Shipped as ConfigMap `polaris-fluent-bit-lua`, **not** through Helm |
| `kustomization.yaml` | the wrapper that makes that ConfigMap. No copy of the script lives in it |
| `apply-lua.sh` | the only supported way to roll a Lua change: context guard → LuaJIT tests v3–v6 + first-tick → `kubectl apply -k` → `rollout restart` → `rollout status` → pod-log check |
| `values.yaml.bak` | an actual backup, from before the OpenSearch cutover. Not current, not a variant |

Everything else about the pipeline — schema, index templates, retention, runbooks, sample documents —
is in [`../logging/`](../logging/README.md). The specification is
[`../logging/SPEC-polaris-audit-logging.ko.md`](../logging/SPEC-polaris-audit-logging.ko.md).

## The three traps

**1. There is no hot reload.** Fluent Bit reads its configuration and its Lua **once, at pod start**.
`kubectl apply -k` on its own updates the ConfigMap and leaves the old script running, with no warning
anywhere — the file inside the pod changes, the process does not re-read it. That is `#13`/`#20`.
`apply-lua.sh` exists so that apply and restart are one step.

**2. A broken Lua stops everything, not just Polaris.** If the script fails filter init at start, every
INPUT pauses and **tier 1 goes down with it** — that is node-wide log collection, for every container in
the cluster (2026-09-15). The LuaJIT tests in `apply-lua.sh` are the gate and are not skippable.
Recovery: check out the previous script and run `apply-lua.sh` again.

**3. Lua and values must move together, in one order.** When a change touches both (a new
`type_int_key`, say):

```bash
bash releases/fluent-bit/apply-lua.sh --no-restart     # ConfigMap first, no restart
bash logging/scripts/step2-render-gate.sh ...  # render gate
helm upgrade --install benchmarks-fluent-bit fluent/fluent-bit \
  --version 0.57.6 -n datahub-hynix -f releases/fluent-bit/values.yaml   # Helm's checksum annotation restarts the pod
```

with **no restart in between**. A pod that comes up with only one half of the change either fails filter
init (new Lua, old config — everything stops) or stores every access line as a parse error (old Lua, new
config). That is `#31`.

A restart always resets Lua state: the next report row is `partial_window: "true"`, `report_seq` returns
to 1, and held lines are lost.

## Verifying a change

`bash logging/scripts/step3-postupgrade.sh` after the roll. It checks the things that fail silently:
ConfigMap sha equals the file sha, the container started *after* the last ConfigMap change, no reloader,
and tier 1 still moving. Index templates are separate — `step9` (report) and `step12` (detail) — and must
be re-applied when a mapping changes.

**Confirm a setting from the running object, never from this directory.** A values file is a statement of
intent; whether it is in effect is a different fact, and in this repo the gap between the two once ran for
months (see CLAUDE.md, *Configuration Policy*).

## Known, unfixed

The tier-1 OUTPUT in `values.yaml` carries an OpenSearch username and password **in plaintext**, against
CLAUDE.md's Zero Hardcoded Credentials rule. Tiers 2 and 3 read theirs from Secret
`opensearch-shipper-credentials`. Moving tier 1 the same way needs that user's `k8s-logs-*` write
permission confirmed first: if it is wrong the output fails with a silent 401 and node-wide collection
stops. Tracked as `SPEC-polaris-audit-logging.ko.md` §11-15 and `.memory/active-issues.md` `#4`.
