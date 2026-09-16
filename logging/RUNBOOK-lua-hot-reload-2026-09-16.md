# RUNBOOK — Lua ConfigMap + hot reload (policy v5)

> **SUPERSEDED 2026-09-16 — hot reload was removed (Kade's decision, `active-issues.md` #28).** Section A
> was run (rev 17: step2/step3/step9/step11 all PASS). **B and C were never run and no longer apply**;
> nothing in C was measured, so do not cite this file for how 5.1.1 handles an invalid reload.
> Fluent Bit now reads the Lua only at start: a Lua change is `bash fluent-bit/apply-lua.sh`
> (tests → `kubectl apply -k` → `rollout restart`). D's question survives in a new shape — tier-1
> `sequence` gaps across a **restart** — and its query below still works for that.
> Kept as the record of what was planned and why.

**Status (original): WRITTEN 2026-09-16, NOTHING RUN.** Written off-cluster by Claude. Every "expect" below is a
prediction from the chart 0.57.6 templates and the Fluent Bit docs, not a measurement. Record each
result in `.memory/active-issues.md` (#28) as it is measured.

What changed (proposal §9.1): the Lua no longer rides in the Helm release via `--set-file`. It is
ConfigMap `polaris-fluent-bit-lua` (from `fluent-bit/kustomization.yaml`), mounted at
`/fluent-bit/polaris-lua/` through `extraVolumes`, and the chart's `hotReload` adds
`--enable-hot-reload` plus a `reloader` sidecar (`configmap-reload` v0.15.0) that POSTs
`localhost:2020/api/v2/reload` when a watched volume changes. With `hotReload.enabled` the chart drops
the `checksum/*` pod annotations, so **Helm config changes reload instead of restarting too**.

Why a runbook and not just a roll: the one failure that already stopped node-wide collection
(2026-09-15, #27) was a Lua filter that failed to load. Hot reload makes loading a new script a
routine, Helm-less act. What 5.1.1 does when the reloaded script is bad is **not documented as
safe** — the docs promise "keeps the previous configuration" only for a failed config-path copy.

Rules for this runbook

* `kubectl config current-context` must print `orbstack` before every section.
* **Section C can stop tier 1 (all container logs, every namespace). Run it only with Kade's explicit
  OK at the moment of execution**, on the local cluster, never in production.
* Nothing here edits `fluent-bit/polaris_access_log.lua` in the repo. Test variants are copies under
  `/tmp`, applied with `kubectl create configmap … --dry-run=client -o yaml | kubectl apply -f -`,
  and **every section ends by re-applying the repo version with `kubectl apply -k fluent-bit/`.**

Shared helpers (paste once per shell):

```bash
NS=datahub-hynix; DS=benchmarks-fluent-bit; CM=polaris-fluent-bit-lua
pod(){ kubectl -n $NS get pods -l app.kubernetes.io/instance=$DS -o jsonpath='{.items[0].metadata.name}'; }
restarts(){ kubectl -n $NS get pod "$(pod)" -o jsonpath='{range .status.containerStatuses[*]}{.name}={.restartCount} {end}'; echo; }
cmsha(){ kubectl -n $NS get cm $CM -o jsonpath='{.data.polaris_access_log\.lua}' | shasum -a 256 | cut -c1-16; }
# port-forward in a second terminal:  kubectl -n $NS port-forward ds/$DS 2020:2020
reloads(){ curl -sS --max-time 5 http://127.0.0.1:2020/api/v2/reload; echo; }
health(){ curl -sS --max-time 5 -o /dev/null -w 'health %{http_code}\n' http://127.0.0.1:2020/api/v1/health; }
push_variant(){ kubectl -n $NS create configmap $CM --from-file=polaris_access_log.lua="$1" \
                  --dry-run=client -o yaml | kubectl apply -f -; }
```

`GET /api/v2/reload` returns the hot-reload counter (`hot_reload_count`). The `fluent-bit` image is
distroless, so `kubectl exec … cat` of the mounted file will probably fail; use the counter, the
reloader log and the pod log instead.

---

## A. First install (v4 → v5). One pod restart, expected.

The new volume and sidecar change the pod spec, so this Helm upgrade restarts the pod once.
Afterwards Lua changes should not.

```bash
cd ~/hynix/local-k8s
cp fluent-bit/polaris_access_log.lua /tmp/polaris.lua
for t in v3 v4 v5; do luajit logging/scripts/test-schema-$t.lua || break; done        # ALL PASS x3
kubectl kustomize fluent-bit/ > /tmp/render-lua.txt
helm upgrade --install benchmarks-fluent-bit fluent/fluent-bit --version 0.57.6 \
  -n datahub-hynix -f fluent-bit/values.yaml --dry-run=client > /tmp/render-after.txt
bash logging/scripts/step2-render-gate.sh /tmp/render-after.txt /tmp/render-lua.txt    # all PASS
kubectl apply -k fluent-bit/                  # ConfigMap FIRST, or the new pod hangs in ContainerCreating
helm upgrade --install benchmarks-fluent-bit fluent/fluent-bit --version 0.57.6 \
  -n datahub-hynix -f fluent-bit/values.yaml
bash logging/scripts/step3-postupgrade.sh
bash logging/scripts/step9-report-index-template.sh          # 41 fields incl. the four v5 ones
```

Pass: step3 all PASS (ConfigMap sha, reloader present, `--enable-hot-reload`, k8s-logs receiving);
pod log has no `[error]`; `kubectl -n $NS logs "$(pod)" -c reloader` shows it watching
`/watch/config`, `/watch/scripts`, `/watch/extra-0`; `reloads` answers with a count (0).

Note in #28: pod name, `restarts`, `reloads`, first report row `schema_version` (5 expected after one window).

## B. Comment-only change → reload without restart

```bash
cp fluent-bit/polaris_access_log.lua /tmp/polaris-b.lua
echo "-- hot reload probe $(date -u +%FT%TZ)" >> /tmp/polaris-b.lua
restarts; reloads; date -u
push_variant /tmp/polaris-b.lua
for i in $(seq 1 24); do sleep 5; printf '%s ' "$(date -u +%T)"; reloads; done     # up to 2 min
restarts
kubectl -n $NS logs "$(pod)" -c reloader --since=5m
kubectl -n $NS logs "$(pod)" -c fluent-bit --since=5m | grep -iE 'reload|lua|error|stop|start' | head -40
```

Expect: `hot_reload_count` +1 within ~60–90 s (kubelet ConfigMap sync + reloader poll); restartCount
unchanged for both containers; the pod log shows the reload and the Lua filters initialising again,
no `[error]`. The next `polaris-report-*` summary row has `report_seq` 1 and `partial_window "true"`
(Lua state reset). k8s-logs keeps receiving (step3 section 4).

Record: seconds from apply to counter change; whether a reload was triggered **once** or more than once
(the reloader sees the ConfigMap's symlink swap; a double reload would mean two state resets).

Restore: `kubectl apply -k fluent-bit/` → counter +1 again → `cmsha` equals `shasum -a 256 fluent-bit/polaris_access_log.lua | cut -c1-16`.

## C. Invalid script — does a bad reload stop the engine? ⚠ needs Kade's OK at execution

This is the question that decides whether hot reload is safe for production. Run it only when a
tier-1 gap of a few minutes on the local cluster is acceptable.

```bash
cp fluent-bit/polaris_access_log.lua /tmp/polaris-c.lua
printf '\nthis is not lua (\n' >> /tmp/polaris-c.lua
luajit -bl /tmp/polaris-c.lua >/dev/null 2>&1 && echo "UNEXPECTED: parses" || echo "broken as intended"
restarts; reloads; health; date -u
push_variant /tmp/polaris-c.lua
for i in $(seq 1 30); do sleep 5; printf '%s ' "$(date -u +%T)"; reloads; health; done
restarts
kubectl -n $NS logs "$(pod)" -c fluent-bit --since=5m | tail -60
bash logging/scripts/step3-postupgrade.sh        # section 4: is k8s-logs still receiving?
```

Outcomes to tell apart, and what each means:

| observed | meaning | production verdict |
|---|---|---|
| reload rejected, old pipeline keeps running, k8s-logs receiving | safe failure | hot reload OK with tests as the gate |
| engine stopped, endpoint dead, liveness probe restarts the pod, pod then crashloops on the bad script | same as #27 but self-inflicted by `kubectl apply` | only with a pre-apply gate that cannot be skipped (CI) |
| engine stopped, pod stays Running, **no restart**, k8s-logs silent | worst: silent outage | do not use hot reload for Lua in production; go back to Helm-rolled Lua |

Recovery, in order — stop at the first that works:

1. `kubectl apply -k fluent-bit/` (good script) → wait 90 s → `reloads`, `health`, step3.
2. If the HTTP server is dead, nothing can receive the reload: `kubectl -n datahub-hynix rollout restart ds/benchmarks-fluent-bit`
   (the pod will read the good ConfigMap applied in step 1).
3. `helm -n datahub-hynix rollback benchmarks-fluent-bit <v4 revision>` — v4 carries its own Lua via the release values.

Record: which row of the table happened, time to detect, time to recover, tier-1 gap
(section D's `sequence` query over the incident interval).

## D. Loss across a (good) reload

Polaris JSON logs carry a per-process `sequence`. Tier 1 stores every Polaris record unfiltered, so a
gap in `sequence` across the reload instant is lost tier-1 data.

1. Start traffic that spans at least 3 windows (polaris-learning `log-coverage/run_traffic.py`, or
   the traffic notebook).
2. In the middle, run section B's `push_variant /tmp/polaris-b.lua`; note the UTC time `T` when
   `hot_reload_count` changed.
3. After traffic ends, pull tier-1 Polaris records from `T-2m` to `T+2m`, sorted by `sequence`, and
   look for holes:

```bash
curl -sS -k -u "$OS_USER:$OS_PASSWORD" "$OS_URL/k8s-logs-*/_search" -H 'Content-Type: application/json' -d '{
  "size": 10000, "_source": ["sequence","@timestamp","kubernetes.pod_name"],
  "query": {"bool": {"filter": [{"exists":{"field":"sequence"}},{"exists":{"field":"loggerName"}},
    {"range":{"@timestamp":{"gte":"<T-2m>","lt":"<T+2m>"}}}]}},
  "sort": [{"sequence":"asc"}]}' \
| python3 -c 'import json,sys
h=[x["_source"] for x in json.load(sys.stdin)["hits"]["hits"]]
s=[int(x["sequence"]) for x in h]
gaps=[(a,b) for a,b in zip(s,s[1:]) if b-a!=1]
print(len(s),"records, seq",s[0] if s else None,"..",s[-1] if s else None,"gaps:",gaps[:20])'
```

   A hole can also be a Polaris pod restart (sequence resets) or two Polaris pods — check
   `kubernetes.pod_name` before calling it loss.
4. For tiers 2/3: `step10` + `step11` on the first **whole** window after `T`. The window containing
   `T` is partial by design (state reset) and is not a loss measurement. `step11` must PASS on the
   next one, and its detail prediction must match.

Pass: no `sequence` gap in tier 1; step11 PASS on the first whole window after the reload.

## E. Rollback of the whole v5 change

```bash
helm -n datahub-hynix history benchmarks-fluent-bit
helm -n datahub-hynix rollback benchmarks-fluent-bit <last v4 revision>   # restores --set-file Lua, no sidecar
git show 7fbea4d:logging/scripts/step3-postupgrade.sh > /tmp/step3-v4.sh && bash /tmp/step3-v4.sh   # v4's step3 (reads the Helm luascripts ConfigMap)
```

ConfigMap `polaris-fluent-bit-lua` is left behind unused after a rollback. Removing it
(`kubectl delete -k fluent-bit/`) is a delete: Kade's explicit OK at the time, and not needed for
the rollback to work.

---

## Open until measured

* C's outcome (the production go/no-go for hot-reloading Lua).
* Reload trigger latency and whether one ConfigMap apply causes one reload or two.
* Whether a Helm config change and a Lua change applied together can reload in the wrong order
  (proposal §9.1-3). Until measured: apply integer-key changes via Helm first, Lua second.
* Filesystem-buffered tiers across reload (tier 2/3 use `storage.path`) vs tier 1 memory buffers.
