# Runbook — removing `polaris-shared-logs-pvc` and the VictoriaLogs leg

**Decision (Kade, 2026-09-18):** the Polaris log PVC goes. Its only two consumers are going with
it — `fb-polaris-shipper`, which tailed the log file into VictoriaLogs, and the Polaris
deployment's own mount. Polaris logs reach OpenSearch from **stdout** through the Fluent Bit
DaemonSet, which never read this volume, so the OpenSearch pipeline is untouched by all of this.

**Repo state vs cluster state.** `polaris/values.yaml` no longer mounts the PVC (committed
2026-09-18). **Nothing below has been run.** Until it is, the cluster still has the mount, the
shipper, VictoriaLogs and the PVC.

> This session cannot reach the cluster. Every command here is Kade's to run, and the two marked
> **DESTRUCTIVE** need explicit authorisation *at the moment of execution* — approving this
> document is not approving those (CLAUDE.md, Destructive Commands Prohibited).

## Why the order is not negotiable

A PVC with a live mounter does not delete. `kubectl delete pvc` returns success, the object
enters `Terminating`, and the `kubernetes.io/pvc-protection` finalizer holds it there until the
last pod referencing it is gone. Delete first and you get something that looks like a hung
cluster and is really just a queue. So: **release every mounter, then delete.**

```
fb-polaris-shipper  ──┐
                      ├──> both release ──> PVC deletable
Polaris deployment  ──┘
```

## Step 0 — preflight (read-only, run it even if you are sure)

```bash
kubectl config current-context                     # MUST be exactly `orbstack`
NS=datahub-hynix

# Who actually mounts it right now? This is the list you must empty.
kubectl -n $NS get pods -o json | python3 -c '
import json,sys
for p in json.load(sys.stdin)["items"]:
    for v in p["spec"].get("volumes",[]):
        c=(v.get("persistentVolumeClaim") or {}).get("claimName")
        if c=="polaris-shared-logs-pvc": print(p["metadata"]["name"])'

kubectl -n $NS get pvc polaris-shared-logs-pvc
helm list -A | grep -E 'fb-polaris-shipper|victoria'   # confirm what is actually installed
```

`helm list -A` matters: the OpenSearch cutover plan said to uninstall the shipper and **nothing
records that it happened** (`REVIEW-pipeline-2026-09-16.md` P10). Confirm, do not assume.

## Step 1 — uninstall the shipper — **DESTRUCTIVE**

```bash
helm uninstall fb-polaris-shipper -n datahub-hynix
kubectl -n datahub-hynix get pods | grep fb-polaris-shipper    # want: nothing
```

What you lose: nothing going forward. `#38` settled that the file handler is off, so the shipper
has been tailing a file that stopped growing at 01:35 on 09-18. What you lose *retrospectively*
is the VictoriaLogs copy of Polaris file logs — see step 2.

## Step 2 — uninstall VictoriaLogs — **DESTRUCTIVE**

VictoriaLogs lives in namespace `logging` (the one namespace CLAUDE.md exempts from
`datahub-hynix`), values in `logging/victoria-values.yaml`, retention 30d on a **50Gi** PVC.

```bash
helm uninstall <release> -n logging          # get the name from `helm list -n logging`
kubectl -n logging get pvc                   # its 50Gi claim does NOT go with the uninstall
```

- Helm does **not** delete PVCs it created from a StatefulSet volumeClaimTemplate. Decide
  deliberately whether the 50Gi claim goes too; it is the last copy of everything the shipper
  ever sent.
- Once this is gone the `logging` namespace is empty. CLAUDE.md's "`logging` holds the log sink
  only" exception then describes nothing — update it in the same commit as the teardown.

## Step 3 — Polaris upgrade, without the mount

The repo is already correct for this; this step just applies it. The pod restarts.

```bash
cd ~/hynix/local-k8s
kubectl config current-context                      # orbstack

helm lint ./polaris
helm upgrade --install benchmarks-polaris ./polaris -n datahub-hynix \
  -f polaris/values.yaml --dry-run=client --debug > /tmp/polaris-render.txt

# The render gate for THIS change: the claim must be gone, and /deployments/logs with it.
grep -c 'polaris-shared-logs-pvc' /tmp/polaris-render.txt     # want 0
grep -c '/deployments/logs'       /tmp/polaris-render.txt     # want 0

helm upgrade --install benchmarks-polaris ./polaris -n datahub-hynix -f polaris/values.yaml
```

Verify against the running object, not the file (CLAUDE.md's Configuration Policy):

```bash
kubectl -n datahub-hynix rollout status deploy/benchmarks-polaris
kubectl -n datahub-hynix get pod -l app.kubernetes.io/name=polaris \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.volumes[*].name}{"\n"}{end}'
# want: no polaris-log-volume on any pod
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- ls /deployments/logs
# want: "No such file or directory" -- the mount is gone, not merely empty
```

**`#39` will interfere.** The HPA flaps on memory at 2% CPU (`0→1→3→2→1` in an hour), so a pod
you just checked may not be the pod that is running. Pin `replicaCount` and disable autoscaling
before this step if you want a stable reading — that is also `#8`'s and `#39`'s standing fix.

## Step 4 — delete the PVC — **DESTRUCTIVE, AND IT TAKES THE ARCHIVE**

Only after step 0's mounter list comes back empty.

```bash
NS=datahub-hynix
kubectl -n $NS get pods -o json | python3 -c '
import json,sys
m=[p["metadata"]["name"] for p in json.load(sys.stdin)["items"]
   for v in p["spec"].get("volumes",[])
   if (v.get("persistentVolumeClaim") or {}).get("claimName")=="polaris-shared-logs-pvc"]
print("STILL MOUNTED BY:",m) if m else print("clear -- safe to delete")'

kubectl -n $NS delete pvc polaris-shared-logs-pvc
kubectl -n $NS get pvc polaris-shared-logs-pvc      # want: NotFound, not Terminating
```

**~27 MB and ~130 rotated `.gz` files going back to 08-21 are destroyed here.** Kade chose this
(2026-09-18): no copy is being kept. It is the only Polaris file-log history older than the
OpenSearch retention, and with `k8s-logs-*` moving to 3 days there will be no raw Polaris lines
older than 3 days anywhere. It also disposes of `#44`'s orphaned-archive problem by disposing of
the archive.

If it sticks in `Terminating`, do **not** remove the finalizer by hand — go back to step 0 and
find the pod still holding it.

## What this closes, and what it does not

| item | after this runbook |
|---|---|
| `#8` — 3 replicas appending to one RWO log file | **closed permanently.** No shared file, no shared rotation state. It fired on 09-18 (`REPLICAS 3`) and can no longer bite |
| `#44` — orphaned dated `.gz` archive no ring can reach | **closed by deletion.** The one-time `find -delete` is no longer needed |
| duplicate mountPath at `/deployments/logs` | **closed.** Chart `logs-storage` + `extraVolumes` could never collide again |
| `#38` — file handler off, file-JSON env vars inert | **closed.** Both variables removed; there is now no volume either |
| `#39` — HPA flapping on memory | **untouched.** Still open, still the reason to pin replicas first |
| OpenSearch pipeline (tiers 1/2/3) | **untouched.** It reads stdout, never this PVC |
| `logging/fb-values.yaml`, `logging/victoria-values.yaml` | **stale after step 2.** Values for releases that no longer exist — delete or mark in the teardown commit |

## Rollback

Steps 1–3 are recoverable: reinstall from `logging/fb-values.yaml` / `logging/victoria-values.yaml`,
and `helm -n datahub-hynix rollback benchmarks-polaris <N>` restores the mount — *provided the PVC
still exists*. **Step 4 is not recoverable.** Once the claim is deleted the data is gone, and
because nothing in this repo ever created that PVC, the repo cannot rebuild it: you would be
hand-making a new empty claim.
