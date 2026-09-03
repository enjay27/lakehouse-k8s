# Runbook: PostgreSQL /dev/shm Exhaustion — OrbStack K8s Leg (S5 pending item)

> Companion to `doc-shm-exhaustion-test-plan.md`. Docker leg already confirmed S1, S2, S4, S5(Docker); S3 did not reproduce (documented, not re-tested here). This runbook only covers the outstanding **OrbStack K8s leg of S5**.
>
> **Run these yourself** in a terminal with `kubectl` pointed at OrbStack — the agent sandbox has no cluster access. Paste back any output/errors and I'll interpret and adjust.
>
> Uses a standalone throwaway pod (`pg-shm-test`), **not** the `postgresql-ha` Helm release — no production chart is touched by this runbook.

---

## 0. Context guard (run first, every time)

```bash
kubectl config current-context
# MUST print exactly: orbstack
# If it doesn't, STOP — do not proceed against the wrong cluster.
```

---

## 1. Repro: deploy pod WITHOUT a /dev/shm override

```bash
cat <<'EOF' | kubectl apply -n datahub-hynix -f -
apiVersion: v1
kind: Pod
metadata:
  name: pg-shm-test
  namespace: datahub-hynix
  labels:
    app: pg-shm-test
    purpose: shm-exhaustion-repro
spec:
  containers:
    - name: postgresql
      image: postgres:16
      env:
        - name: POSTGRES_PASSWORD
          value: test
      # NOTE: intentionally NO /dev/shm mount — mirrors production default (64MB tmpfs)
EOF

kubectl wait -n datahub-hynix --for=condition=Ready pod/pg-shm-test --timeout=120s
kubectl exec -n datahub-hynix pg-shm-test -- df -h /dev/shm
# expect ~64M
```

---

## 2. Data setup + force parallel plan

kubectl exec sessions don't persist SET state across separate invocations (same caveat your Docker leg hit) — so data setup can be its own exec, but the SET + trigger query must be combined into one `-c` string later.

```bash
kubectl exec -n datahub-hynix pg-shm-test -- psql -U postgres -c "
CREATE TABLE big_a AS
  SELECT g AS id, md5(g::text) AS payload, g % 1000 AS join_key
  FROM generate_series(1, 5000000) g;

CREATE TABLE big_b AS
  SELECT g AS id, md5(g::text) AS payload, g % 1000 AS join_key
  FROM generate_series(1, 5000000) g;

ANALYZE big_a;
ANALYZE big_b;
"
```

Verify a parallel plan is chosen:

```bash
kubectl exec -n datahub-hynix pg-shm-test -- psql -U postgres -c "
SET max_parallel_workers_per_gather = 4;
SET parallel_setup_cost = 0;
SET parallel_tuple_cost = 0;
SET min_parallel_table_scan_size = 0;
SET work_mem = '32MB';
EXPLAIN SELECT count(*) FROM big_a a JOIN big_b b USING (join_key) WHERE a.id % 7 = 0;
"
# MUST show: Parallel Hash Join + Workers Planned: 4
```

---

## 3. Trigger + live observation

Open a second terminal tab/window for the observer:

```bash
# Terminal 1 (observer — start first, leave running)
kubectl exec -n datahub-hynix pg-shm-test -- sh -c 'watch -n0.5 "df -h /dev/shm; ls -lh /dev/shm"'
```

```bash
# Terminal 2 (trigger)
kubectl exec -n datahub-hynix pg-shm-test -- psql -U postgres -c "
SET max_parallel_workers_per_gather = 4;
SET parallel_setup_cost = 0;
SET parallel_tuple_cost = 0;
SET min_parallel_table_scan_size = 0;
SET work_mem = '32MB';
SELECT count(*) FROM big_a a JOIN big_b b USING (join_key) WHERE a.id % 7 = 0;
"
```

Expected: `PostgreSQL.xxxxxx` files appear/grow in the observer pane, query fails with:
```
ERROR:  could not resize shared memory segment "..." to ... bytes: No space left on device
```

Capture server-side evidence:

```bash
kubectl logs -n datahub-hynix pg-shm-test | grep -i "shared memory"
```

This confirms **S5 repro-without-fix** on K8s (mirrors S1/S2 already proven in Docker — no need to re-litigate S3, already documented as non-reproducing).

---

## 4. Apply the fix and verify (S5 — the actual pending criterion)

Delete and redeploy with the production-mirror fix (`Memory` emptyDir, `sizeLimit: 2Gi` — same as the proposed `postgresql-ha` chart change):

```bash
kubectl delete pod -n datahub-hynix pg-shm-test

cat <<'EOF' | kubectl apply -n datahub-hynix -f -
apiVersion: v1
kind: Pod
metadata:
  name: pg-shm-test
  namespace: datahub-hynix
  labels:
    app: pg-shm-test
    purpose: shm-exhaustion-fix-verify
spec:
  volumes:
    - name: dshm
      emptyDir:
        medium: Memory
        sizeLimit: 2Gi
  containers:
    - name: postgresql
      image: postgres:16
      env:
        - name: POSTGRES_PASSWORD
          value: test
      volumeMounts:
        - name: dshm
          mountPath: /dev/shm
EOF

kubectl wait -n datahub-hynix --for=condition=Ready pod/pg-shm-test --timeout=120s
kubectl exec -n datahub-hynix pg-shm-test -- df -h /dev/shm
# MUST show 2.0G
```

Recreate data and rerun the identical trigger:

```bash
kubectl exec -n datahub-hynix pg-shm-test -- psql -U postgres -c "
CREATE TABLE big_a AS SELECT g AS id, md5(g::text) AS payload, g % 1000 AS join_key FROM generate_series(1, 5000000) g;
CREATE TABLE big_b AS SELECT g AS id, md5(g::text) AS payload, g % 1000 AS join_key FROM generate_series(1, 5000000) g;
ANALYZE big_a; ANALYZE big_b;
"

kubectl exec -n datahub-hynix pg-shm-test -- psql -U postgres -c "
SET max_parallel_workers_per_gather = 4;
SET parallel_setup_cost = 0;
SET parallel_tuple_cost = 0;
SET min_parallel_table_scan_size = 0;
SET work_mem = '32MB';
SELECT count(*) FROM big_a a JOIN big_b b USING (join_key) WHERE a.id % 7 = 0;
"
# MUST succeed with a count, no error
```

If this succeeds → **S5 fully confirmed** (Docker leg + K8s leg both done).

---

## 5. Cleanup

```bash
kubectl delete pod -n datahub-hynix pg-shm-test
```

(This deletes only the throwaway test pod — not a namespace, not a Helm release. Still, confirm with me before running if you want a second check.)

---

## 6. After you paste back results

I'll then:
- Append a §10-style results block to `doc-shm-exhaustion-test-plan.md` (or wherever you want it filed in-repo)
- Note the confirmed fix in a `postgresql-shm-incident-analysis.md` if you want one created
- Update `MEMORY.md` Task 1 status
- Draft (not apply) the actual `postgresql/values.yaml` change — adding the same `dshm` emptyDir volume/mount to the `postgresql-ha` release — as a **separate** plan for your sign-off, since that touches the committed production chart.
