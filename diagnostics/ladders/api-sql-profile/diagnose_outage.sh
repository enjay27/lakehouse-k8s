#!/usr/bin/env bash
# Why is Polaris refusing connections? Read-only. Changes nothing.
#
#   ./diagnose_outage.sh
#
# "Connection refused" on 8181 is NOT connection exhaustion at the Polaris
# layer -- an exhausted server accepts the socket and then fails the request.
# Refused means nothing is listening, which on Kubernetes almost always means
# the pod is not Ready, so the Service has no endpoints. The usual chain is:
#
#     Polaris cannot get a DB connection
#       -> readiness probe fails
#         -> Service drops the endpoint
#           -> LoadBalancer refuses on 8181
#
# So the question is never "is Polaris overloaded", it is "why can Polaris not
# talk to PostgreSQL". This script gathers the evidence for that in one pass,
# in the order the chain runs.

set -uo pipefail

NS="${POLARIS_K8S_NAMESPACE:-datahub-hynix}"
DEPLOY="${POLARIS_K8S_DEPLOYMENT:-benchmarks-polaris}"
PGHOST="${PG_HOST:-192.168.139.2}"
PGPORT="${PG_PORT:-5432}"
PGUSER="${PG_USER:-polaris}"
PGDB="${PG_DB:-polaris}"

hr() { printf '\n%s\n%s\n%s\n' "==============================================================" "$1" "=============================================================="; }

# Resolve the Polaris pod BY NAME, not by a guessed label and not by
# `.items[0]`. The first run of this script did both: the label selector
# matched nothing (so the `||` fallback never fired, because kubectl exits 0 on
# "No resources found"), and `.items[0]` picked whatever sorts first in the
# namespace -- fluent-bit. Sections 3, 4 and 5 then reported that pod's restart
# count and logs under a Polaris heading. Wrong pod, confident output.
POD=$(kubectl get pods -n "$NS" -o name 2>/dev/null | grep -i "polaris" | grep -vi "fluent\|shipper" | head -1)
POD="${POD#pod/}"

hr "1. IS THE POD EVEN RUNNING?"
echo "-- every pod in the namespace, with restart counts:"
kubectl get pods -n "$NS" -o wide 2>/dev/null
echo
echo "-- resolved polaris pod: ${POD:-<none found>}"
echo
echo "-- deployment:"
kubectl get deploy "$DEPLOY" -n "$NS" 2>/dev/null

hr "2. DOES THE SERVICE HAVE ENDPOINTS?"
# No endpoints is the direct cause of "connection refused". If this is empty,
# stop reading the PostgreSQL sections and find out why the pod is unready.
kubectl get endpoints -n "$NS" 2>/dev/null | head -20

hr "3. WHY IS IT UNREADY? (events, restarts, OOM)"
if [ -n "${POD:-}" ]; then
  kubectl get pod "$POD" -n "$NS" \
    -o jsonpath='restarts={.status.containerStatuses[0].restartCount}{"\n"}lastState={.status.containerStatuses[0].lastState}{"\n"}' 2>/dev/null
  echo
  kubectl describe pod "$POD" -n "$NS" 2>/dev/null | sed -n '/Events:/,$p' | head -25
fi

hr "4. WHAT DID IT SAY BEFORE IT DIED?"
# --previous reads the CRASHED container, not the one that replaced it. Without
# it you read a fresh log that has not hit the problem yet.
echo "-- previous container, filtered to the things that matter:"
kubectl logs "$POD" -n "$NS" --previous --tail=4000 2>/dev/null \
  | grep -Ei "shared memory|No space left|OutOfMemory|OOM|Connection refused|too many clients|08001|08003|08006|SQLState|Unable to acquire|pool|FATAL" \
  | tail -40
echo
echo "-- current container, same filter:"
kubectl logs "$POD" -n "$NS" --tail=2000 2>/dev/null \
  | grep -Ei "shared memory|No space left|OutOfMemory|OOM|too many clients|08001|08003|08006|SQLState|Unable to acquire|pool|FATAL" \
  | tail -20

hr "5. /dev/shm  --  THE ONE THIS REPO HAS ALREADY DOCUMENTED"
# diagnostics/doc-shm-exhaustion-test-plan.md reproduced this exact failure:
# a container's default 64MB /dev/shm, a PARALLEL query allocating dynamic
# shared memory, "could not resize shared memory segment ... No space left on
# device", surfacing to clients as 08001/08003/08006.
#
# That is directly relevant right now. An unindexed grantee lookup over ~580k
# grant_records escalates to a Parallel Seq Scan on EVERY authenticated
# request. 02b already measured the escalation at ~233k rows. So the sweep's
# index-absent cells are precisely the load that plan was written to reproduce.
if [ -n "${POD:-}" ]; then
  echo "-- polaris pod:"; kubectl exec "$POD" -n "$NS" -- df -h /dev/shm 2>/dev/null
fi
for p in $(kubectl get pods -n "$NS" -o name 2>/dev/null | grep -Ei "postgres|pg|patroni|repmgr" | head -3); do
  echo "-- $p:"; kubectl exec -n "$NS" "${p#pod/}" -- df -h /dev/shm 2>/dev/null
done

hr "6. POSTGRESQL: IS IT ACTUALLY OUT OF CONNECTIONS?"
# Answer this with numbers before changing any setting. This repo has a
# standing rule -- an earlier multi-setting PostgreSQL change took the whole HA
# cluster down and forced a full OrbStack reset -- so config changes need
# explicit sign-off and a measured reason, not an inference from a refused TCP
# connection on a different port.
# psql is not necessarily on the workstation. Run it INSIDE the PostgreSQL
# pod, which certainly has it -- and which also means these numbers come from
# the primary rather than through Pgpool's load balancer.
PGPOD=$(kubectl get pods -n "$NS" -o name 2>/dev/null | grep -E "postgresql-[0-9]+$" | head -1)
PGPOD="${PGPOD#pod/}"
if [ -z "${PGPOD:-}" ]; then
  echo "no postgresql pod found; skipping the PostgreSQL section"
  PSQL="true"
else
  echo "-- querying inside $PGPOD"
  PSQL="kubectl exec -n $NS $PGPOD -- env PGPASSWORD=${PG_PASSWORD:-polaris} psql -U $PGUSER -d $PGDB -X -q -A"
fi
$PSQL -c "SELECT current_setting('max_connections') AS max_connections,
                 count(*)                          AS in_use,
                 count(*) FILTER (WHERE state='idle')              AS idle,
                 count(*) FILTER (WHERE state='idle in transaction') AS idle_in_txn
          FROM pg_stat_activity" 2>&1 | head -5
echo
echo "-- by application:"
$PSQL -c "SELECT coalesce(application_name,'(none)') app, state, count(*)
          FROM pg_stat_activity GROUP BY 1,2 ORDER BY 3 DESC LIMIT 10" 2>&1 | head -12
echo
echo "-- parallel workers (the /dev/shm consumer):"
$PSQL -c "SELECT current_setting('max_parallel_workers_per_gather') AS per_gather,
                 current_setting('max_parallel_workers')            AS total,
                 current_setting('max_worker_processes')            AS processes" 2>&1 | head -4
echo
echo "-- replication:"
$PSQL -c "SELECT application_name, state,
                 pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS behind_bytes
          FROM pg_stat_replication" 2>&1 | head -6

hr "READ IT IN THIS ORDER"
cat <<'NOTE'
  Section 2 empty  -> the Service has no endpoints. That IS the refusal.
                      Everything below is about WHY, not about load.

  Section 4 shows "could not resize shared memory segment" or 08001/08003/08006
                   -> /dev/shm exhaustion under parallel query. Do NOT raise
                      max_connections; that makes it worse. The fix is either
                      more shm on the PostgreSQL container (--shm-size / an
                      emptyDir sized medium=Memory) or stopping the escalation:
                         SWEEP_PIN_PARALLELISM=1
                      which is an ALTER ROLE, session-scoped and reversible,
                      not an ALTER SYSTEM.

  Section 4 shows OOMKilled / lastState.terminated.reason
                   -> Polaris ran out of heap. Raise its memory limit, or lower
                      the sweep's concurrency. Nothing to do with PostgreSQL.

  Section 6 shows in_use at or near max_connections
                   -> now, and only now, is "limit concurrent connections" the
                      right conversation. Prefer capping the CLIENT (Polaris
                      pool size, sweep concurrency) over raising the server:
                      raising max_connections raises per-backend memory and is
                      how this cluster went down before.
NOTE
