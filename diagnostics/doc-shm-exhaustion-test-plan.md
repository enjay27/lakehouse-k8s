# Test Plan: PostgreSQL /dev/shm Exhaustion — Local Reproduction

> **Status:** Docker leg executed and verified (2026-07-09) — S1, S2, S4, S5(Docker) confirmed; S3 did not reproduce (documented finding, see §10). OrbStack K8s leg of S5 (production-mirror manifest) still pending, to be run separately. This reproduction uses plain Docker/Kubernetes + `psql`, outside the `src`/`init_env`/notebook model this repo otherwise uses (it is not Polaris-specific and was executed manually on the host Mac, not in a sandboxed shell). See §10 for full results.
>
> **Purpose:** Reproduce the production incident (container `/dev/shm` 64MB default → parallel query DSM allocation failure → connection loss → client SQL-STATE 08001/08003/08006) locally, then verify the fix.
>
> **Environment:** M-series MacBook — Docker (fast iteration) and/or OrbStack Kubernetes (production-mirror).

---

## 1. Background

- Production PostgreSQL runs on Kubernetes with **no `/dev/shm` override** → container default **64MB tmpfs**.
- PostgreSQL uses `dynamic_shared_memory_type = posix` (default) → **parallel query** DSM segments are created as files in `/dev/shm/PostgreSQL.xxxxxx`.
- Production config: `shared_buffers=64GB`, `effective_cache_size=192GB`, `work_mem=32MB`, `maintenance_work_mem=4GB`. **None of these use /dev/shm** — only parallel DSM does.
- Failure: parallel hash join with work_mem 32MB × several workers exceeds 64MB → `ERROR: could not resize shared memory segment ... No space left on device` → backend crash → client (Apache Polaris) sees 08001/08003/08006.
- Planned production fix: Memory-medium emptyDir mounted at `/dev/shm` with `sizeLimit: 2Gi`, deployed via Bitbucket → Jenkins → ArgoCD.

**Key hypothesis to prove:** the trigger is *parallel query DSM*, NOT large result sets. A huge non-parallel SELECT should NOT fail. This distinction goes in the incident handoff.

---

## 2. Success Criteria

| # | Criterion |
|---|---|
| S1 | Reproduce `could not resize shared memory segment ... No space left on device` deterministically with small /dev/shm |
| S2 | Observe DSM segments (`/dev/shm/PostgreSQL.*`) appearing/growing live during the failing query |
| S3 | Reproduce downstream connection-loss symptom on a concurrent client session (08006 analog) |
| S4 | Negative control passes: non-parallel large-resultset query succeeds under the same small /dev/shm |
| S5 | Fix verified: same trigger query succeeds with /dev/shm = 2Gi (Docker `--shm-size` AND K8s Memory emptyDir) |

---

## 3. Phase 0 — Environments

### Option A: Docker (start here — fastest)

```bash
docker run -d --name pg-shm-test --shm-size=16m \
  -e POSTGRES_PASSWORD=test -p 5433:5432 postgres:16
```

- `--shm-size=16m`: smaller than production's 64MB → faster, deterministic reproduction.
- Connect: `psql "host=localhost port=5433 user=postgres password=test"`

### Option B: OrbStack K8s (production mirror — use for Phase 5 fix verification)

Deploy a minimal PostgreSQL pod **without** any dshm volume (inherits the 64MB default, same as production):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pg-shm-test
spec:
  containers:
    - name: postgresql
      image: postgres:16
      env:
        - name: POSTGRES_PASSWORD
          value: test
      # NOTE: intentionally NO /dev/shm mount — reproduces production state
```

---

## 4. Phase 1 — Data Setup

```sql
CREATE TABLE big_a AS
  SELECT g AS id, md5(g::text) AS payload, g % 1000 AS join_key
  FROM generate_series(1, 5000000) g;

CREATE TABLE big_b AS
  SELECT g AS id, md5(g::text) AS payload, g % 1000 AS join_key
  FROM generate_series(1, 5000000) g;

ANALYZE big_a;
ANALYZE big_b;
```

(~2 × 400MB tables; adjust row count down if disk-constrained, up if reproduction is flaky.)

---

## 5. Phase 2 — Force Parallel Plan (session-level)

```sql
SET max_parallel_workers_per_gather = 4;
SET parallel_setup_cost = 0;
SET parallel_tuple_cost = 0;
SET min_parallel_table_scan_size = 0;
SET work_mem = '32MB';   -- match production
```

Verify before triggering:

```sql
EXPLAIN SELECT count(*) FROM big_a a JOIN big_b b USING (join_key) WHERE a.id % 7 = 0;
-- MUST show: Parallel Hash Join + Workers Planned: 4
```

If no parallel plan appears, check `max_parallel_workers` and `max_worker_processes` (server-level, may need container restart with `-c` flags).

---

## 6. Phase 3 — Trigger + Live Observation

Terminal 1 (observer, start first):

```bash
docker exec pg-shm-test sh -c 'watch -n0.5 "df -h /dev/shm; ls -lh /dev/shm"'
```

Terminal 2 (trigger):

```sql
SELECT count(*) FROM big_a a
JOIN big_b b USING (join_key)
WHERE a.id % 7 = 0;
```

**Expected:** `PostgreSQL.xxxxxx` segments appear in observer → grow → query fails with `could not resize shared memory segment ... No space left on device` (→ S1, S2).

If a single query does not trip 16MB, run concurrently:

```bash
for i in $(seq 4); do
  psql "host=localhost port=5433 user=postgres password=test" \
    -c "SET max_parallel_workers_per_gather=4; SET parallel_setup_cost=0; SET parallel_tuple_cost=0; SET min_parallel_table_scan_size=0; SET work_mem='32MB'; SELECT count(*) FROM big_a a JOIN big_b b USING (join_key) WHERE a.id % 7 = 0;" &
done; wait
```

Also capture the server-side log line:

```bash
docker logs pg-shm-test 2>&1 | grep -i "shared memory"
```

---

## 7. Phase 4 — Downstream Symptom (08xxx analog)

Goal: show that DSM failure can poison *other* connections, matching the Polaris causal chain (→ S3).

1. Open 2–3 idle psql sessions (or a small Python/psycopg connection-pool script) and keep them running simple periodic queries (`SELECT 1` loop).
2. Repeatedly fire the Phase 3 trigger until a backend crash occurs (watch `docker logs` for `terminating connection because of crash of another server process` — this is PostgreSQL's crash-recovery killing all backends).
3. Observe the idle sessions receive connection-terminated errors → this is the client-side 08006 equivalent.

Note: a *clean* DSM failure only errors the one query; the connection-loss cascade requires an actual backend crash/recovery cycle. Both outcomes are worth recording — clean failure alone already explains Polaris request errors; crash-recovery explains pool-wide 08003/08006.

---

## 8. Phase 5 — Fix Verification

### Docker

```bash
docker rm -f pg-shm-test
docker run -d --name pg-shm-test --shm-size=2g \
  -e POSTGRES_PASSWORD=test -p 5433:5432 postgres:16
# rerun Phase 1 + 2 + 3 → trigger query must SUCCEED
```

### OrbStack K8s (validates the exact production manifest change)

```yaml
spec:
  volumes:
    - name: dshm
      emptyDir:
        medium: Memory
        sizeLimit: 2Gi
  containers:
    - name: postgresql
      volumeMounts:
        - name: dshm
          mountPath: /dev/shm
```

Rerun trigger inside the pod → success (→ S5). Confirm with `kubectl exec pg-shm-test -- df -h /dev/shm` showing 2.0G.

---

## 9. Phase 6 — Negative Control

Same small-shm environment:

```sql
SET max_parallel_workers_per_gather = 0;  -- disable parallelism
SELECT * FROM big_a;                       -- huge result set, no DSM
```

**Expected:** succeeds (slow, but no shm error) → proves failure mode is parallel DSM, not result-set size (→ S4).

---

## 10. Results (2026-07-09, Docker leg)

Environment: Docker Desktop/OrbStack container, `postgres:16`, `--shm-size=16m` (repro) / `--shm-size=2g` (fix). All commands run via `docker exec` (no host `psql` client needed — image ships one).

| Criterion | Status | Evidence |
|---|---|---|
| S1 — deterministic repro | ✅ confirmed | `ERROR: could not resize shared memory segment "/PostgreSQL.1910491080" to 67244032 bytes: No space left on device` — reproduced on first trigger, no flakiness observed. |
| S2 — DSM segments observed live | ✅ confirmed | `watch df -h /dev/shm` showed `PostgreSQL.*` files appear and grow (e.g. `PostgreSQL.392054418` at 1.0M) right up to the 16M ceiling during the query. |
| S3 — connection-loss cascade | ❌ did not reproduce | Repeated single triggers and a 5-round × 4-concurrent load loop both produced only clean per-backend `ERROR`s (`could not resize shared memory segment`, `could not map dynamic shared memory segment`) — no `PANIC`, no `crash of another server process`, confirmed via `grep -iE "crash\|PANIC\|terminating connection"` on the container logs (empty). An idle third session (`SELECT 1` loop) was never affected. **Finding:** on Postgres 16 in this container, DSM/ENOSPC exhaustion fails gracefully per-backend and does not trigger crash-recovery — S3 needs a different trigger (e.g. actual container OOM-kill) to reproduce the 08006-style cascade; the clean-failure mode alone already fully explains Polaris-side 08001/08003. |
| S4 — negative control passes | ✅ confirmed | Same 16m-shm container, `max_parallel_workers_per_gather=0`, `SELECT count(*) FROM big_a` (5M rows, no DSM/parallelism involved) → `5000000` rows, no error. Confirms failure mode is parallel-DSM-specific, not result-set size. |
| S5 — fix verified (Docker) | ✅ confirmed | Rebuilt container with `--shm-size=2g`, recreated `big_a`/`big_b`, reran the identical trigger query → `count = 3571425000`, no error. |
| S5 — fix verified (OrbStack K8s) | ⏳ pending | Production-mirror manifest validation (Memory-medium emptyDir, `sizeLimit: 2Gi`) not yet run — user to execute separately per §8. |

- Exact error line (client): `ERROR:  could not resize shared memory segment "/PostgreSQL.1910491080" to 67244032 bytes: No space left on device`
- Exact error lines (`docker logs`):
  ```
  2026-07-09 00:56:33.723 UTC [365] ERROR:  could not resize shared memory segment "/PostgreSQL.1910491080" to 67244032 bytes: No space left on device
  2026-07-09 00:56:33.724 UTC [366] ERROR:  could not map dynamic shared memory segment
  2026-07-09 00:56:33.724 UTC [367] ERROR:  could not map dynamic shared memory segment
  2026-07-09 00:56:33.724 UTC [368] ERROR:  could not map dynamic shared memory segment
  2026-07-09 00:56:33.724 UTC [369] ERROR:  could not map dynamic shared memory segment
  ```
- `EXPLAIN` output showing Parallel Hash Join:
  ```
  Finalize Aggregate  (cost=314251.66..314251.67 rows=1 width=8)
    ->  Gather  (cost=314251.64..314251.65 rows=4 width=8)
          Workers Planned: 4
          ->  Partial Aggregate  (cost=314251.64..314251.65 rows=1 width=8)
                ->  Parallel Hash Join  (cost=74909.00..236146.47 rows=31242069 width=0)
                      Hash Cond: (a.join_key = b.join_key)
                      ->  Parallel Seq Scan on big_a a  (cost=0.00..65532.30 rows=6250 width=4)
                            Filter: ((id % 7) = 0)
                      ->  Parallel Hash  (cost=59284.00..59284.00 rows=1250000 width=4)
                            ->  Parallel Seq Scan on big_b b  (cost=0.00..59284.00 rows=1250000 width=4)
  ```
- Notes / deviations from plan:
  - No host `psql` client was available; all queries ran via `docker exec -it pg-shm-test psql -U postgres -c "..."`. Each `-c` invocation is its own connection/session, so `SET` params and the query they affect had to be combined into a single invocation (session-scoped `SET`s don't persist across separate `docker exec` calls).
  - Used `count(*)` instead of `SELECT *` for the S4 negative control to avoid dumping 5M rows to the terminal — equivalent proof (non-parallel, no DSM).
  - S3 required an explicit escalation attempt (5 rounds × 4 concurrent triggers) beyond a single query before concluding non-reproduction; documented as a real result, not a skipped step.

Still open: OrbStack K8s leg of S5. Feed these findings into `postgresql-shm-incident-analysis.md` (section 4 evidence checklist + section 6 lessons) — in particular the S3 non-reproduction, since it affects how confidently the incident writeup can claim the DSM-exhaustion theory explains the *connection-loss* symptom specifically (vs. the query-error symptom, which is now solidly proven).

## 11. Cleanup

```bash
docker rm -f pg-shm-test
# kubectl delete pod pg-shm-test
```
