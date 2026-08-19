#!/usr/bin/env bash
# =============================================================================
# capture_pg_startup_error.sh
# =============================================================================
# Get the REAL error behind Bitnami's useless
#   "postgresql-repmgr ... ERROR ==> PostgreSQL is not ready after 60 seconds"
#
# WHY THIS IS NEEDED
# ------------------
# The Bitnami entrypoint starts postgres with `pg_ctl -l $POSTGRESQL_LOG_FILE`,
# i.e. output redirected to a FILE inside the container:
#
#     /opt/bitnami/postgresql/logs/postgresql.log
#
# So `kubectl logs` shows the wrapper's chatter and NOTHING from postgres
# itself. The container then dies and takes the file with it.
#
# This script polls `kubectl exec` during the ~60s window the container is
# alive, grabs that log the moment it is readable, and also captures the
# effective configuration for comparison against a healthy node.
#
# Usage:
#   ./capture_pg_startup_error.sh                       # auto-detect failing pod
#   ./capture_pg_startup_error.sh <pod-name>
#   NS=other-ns ./capture_pg_startup_error.sh
#
# Output: ./pg-startup-capture-<pod>-<timestamp>/
# =============================================================================
set -uo pipefail

NS="${NS:-datahub-hynix}"
STS_PREFIX="${STS_PREFIX:-benchmarks-postgresql-postgresql-ha-postgresql}"
POD="${1:-}"
PG_LOG="/opt/bitnami/postgresql/logs/postgresql.log"
PG_CONF="/opt/bitnami/postgresql/conf/postgresql.conf"
PG_HBA="/opt/bitnami/postgresql/conf/pg_hba.conf"

# ---- find the failing pod ---------------------------------------------------
if [[ -z "$POD" ]]; then
  POD=$(kubectl -n "$NS" get pods -o \
    jsonpath="{range .items[?(@.status.phase!=\"Succeeded\")]}{.metadata.name}{\" \"}{.status.containerStatuses[0].ready}{\"\n\"}{end}" \
    2>/dev/null | awk -v p="$STS_PREFIX" '$1 ~ p && $2 == "false" {print $1; exit}')
fi
if [[ -z "$POD" ]]; then
  echo "No unready pod matching '$STS_PREFIX' found in namespace $NS."
  echo "Current state:"
  kubectl -n "$NS" get pods | grep -E "NAME|$STS_PREFIX"
  echo
  echo "If nothing is failing, there is nothing to capture — good news."
  exit 0
fi

OUT="./pg-startup-capture-${POD}-$(date +%H%M%S)"
mkdir -p "$OUT"
echo "namespace : $NS"
echo "pod       : $POD"
echo "output    : $OUT"
echo

# ---- always-available context ----------------------------------------------
kubectl -n "$NS" get pods            > "$OUT/pods.txt" 2>&1
kubectl -n "$NS" describe pod "$POD" > "$OUT/describe.txt" 2>&1
kubectl -n "$NS" logs "$POD" --tail=-1            > "$OUT/wrapper-current.log"  2>&1
kubectl -n "$NS" logs "$POD" --previous --tail=-1 > "$OUT/wrapper-previous.log" 2>&1
echo "[*] wrapper logs + describe captured"

# ---- race the crash window --------------------------------------------------
# CrashLoopBackOff grows the gap between attempts (10s, 20s, 40s...), so poll
# patiently rather than assuming the container is up right now.
echo "[*] polling for the postgres log (container is only alive ~60s per attempt)"
GOT=0
for i in $(seq 1 180); do
  if kubectl -n "$NS" exec "$POD" -c postgresql -- \
       sh -c "test -s '$PG_LOG'" >/dev/null 2>&1; then

    kubectl -n "$NS" exec "$POD" -c postgresql -- \
      sh -c "tail -300 '$PG_LOG'" > "$OUT/postgresql.log" 2>&1
    kubectl -n "$NS" exec "$POD" -c postgresql -- \
      sh -c "cat '$PG_CONF'" > "$OUT/postgresql.conf" 2>&1
    kubectl -n "$NS" exec "$POD" -c postgresql -- \
      sh -c "cat '$PG_HBA'" > "$OUT/pg_hba.conf" 2>&1
    kubectl -n "$NS" exec "$POD" -c postgresql -- \
      sh -c "df -h /dev/shm; echo; free -m" > "$OUT/resources.txt" 2>&1
    GOT=1
    echo "[+] captured on attempt $i"
    break
  fi
  sleep 1
done

if [[ "$GOT" == "0" ]]; then
  echo "[!] could not read $PG_LOG — the container never stayed up long enough."
  echo "    Fallback: make postgres log to the PVC instead of container-local"
  echo "    storage, so the log survives the crash. Add to extendedConf:"
  echo
  echo "        logging_collector = on"
  echo "        log_directory = 'log'"
  echo "        log_filename = 'postgresql-%Y-%m-%d.log'"
  echo
  echo "    PGDATA lives on the PVC, so the log then persists and can be read by"
  echo "    scaling the StatefulSet down and mounting the PVC in a debug pod."
fi

# ---- healthy peer, for comparison ------------------------------------------
PEER=$(kubectl -n "$NS" get pods -o \
  jsonpath="{range .items[*]}{.metadata.name}{\" \"}{.status.containerStatuses[0].ready}{\"\n\"}{end}" \
  2>/dev/null | awk -v p="$STS_PREFIX" '$1 ~ p && $2 == "true" {print $1; exit}')
if [[ -n "$PEER" ]]; then
  echo "[*] capturing healthy peer $PEER for diff"
  kubectl -n "$NS" exec "$PEER" -c postgresql -- sh -c "cat '$PG_CONF'" \
    > "$OUT/peer-postgresql.conf" 2>&1
  kubectl -n "$NS" exec "$PEER" -c postgresql -- sh -c "cat '$PG_HBA'" \
    > "$OUT/peer-pg_hba.conf" 2>&1
  kubectl -n "$NS" exec "$PEER" -c postgresql -- \
    env PGUSER=postgres PGPASSWORD="${PGPASSWORD:-polaris}" \
    psql -Atc "SELECT name||' = '||setting FROM pg_settings
               WHERE name IN ('max_connections','shared_buffers','max_worker_processes',
                              'max_wal_senders','max_locks_per_transaction',
                              'max_prepared_transactions','shared_preload_libraries')" \
    > "$OUT/peer-settings.txt" 2>&1
fi

# ---- summarise --------------------------------------------------------------
echo
echo "================ LIKELY CAUSE ================"
if [[ -s "$OUT/postgresql.log" ]]; then
  # A standby refuses to start when any of these is LOWER than on the primary.
  if grep -qiE 'insufficient parameter settings|lower setting than on the primary' "$OUT/postgresql.log"; then
    echo ">> STANDBY PARAMETER MISMATCH"
    grep -iE -A3 'insufficient parameter settings|lower setting' "$OUT/postgresql.log" | head -20
    echo
    echo "   A hot standby needs max_connections / max_worker_processes /"
    echo "   max_locks_per_transaction / max_prepared_transactions >= the primary's."
    echo "   During a rolling update the nodes disagree — let the rollout finish,"
    echo "   or restart the primary so every node lands on the same values."
  elif grep -qiE 'no pg_hba.conf entry' "$OUT/postgresql.log"; then
    echo ">> PG_HBA REJECTION (check for an IPv6 address — 0.0.0.0/0 is IPv4 ONLY)"
    grep -iE -B1 -A2 'no pg_hba.conf entry' "$OUT/postgresql.log" | head -20
  elif grep -qiE 'could not resize shared memory|No space left on device' "$OUT/postgresql.log"; then
    echo ">> SHARED MEMORY / /dev/shm EXHAUSTION"
    grep -iE 'shared memory|No space left' "$OUT/postgresql.log" | head -10
  elif grep -qiE 'requested WAL segment .* has already been removed|could not receive data from WAL stream' "$OUT/postgresql.log"; then
    echo ">> WAL GONE — the standby is too far behind to catch up."
    echo "   Needs a fresh clone: delete this pod's PVC and let it re-clone."
  else
    echo ">> No known pattern matched. Last FATAL/PANIC/ERROR lines:"
    grep -iE 'FATAL|PANIC|ERROR' "$OUT/postgresql.log" | tail -20
  fi
else
  echo "postgres log not captured — see the fallback above."
  echo "Wrapper log tail:"
  tail -20 "$OUT/wrapper-previous.log" 2>/dev/null
fi

echo
echo "============== CONFIG DIFF vs PEER =============="
if [[ -s "$OUT/postgresql.conf" && -s "$OUT/peer-postgresql.conf" ]]; then
  diff "$OUT/peer-postgresql.conf" "$OUT/postgresql.conf" \
    && echo "(identical — the config is not the difference)"
else
  echo "(need both the failing pod's and a healthy peer's conf to diff)"
fi

echo
echo "Everything saved to: $OUT"
