#!/usr/bin/env bash
# Drop, bootstrap, RESTART, wait, verify -- one command, restart never skipped.
#
#   ./reset_realm.sh                 # full reset to a clean bootstrapped realm
#   ./reset_realm.sh --seed 50       # ...then seed 50 users and upgrade grants
#
# WHY THIS EXISTS
# ---------------
# Three separate failures this session -- a stale entity cache serving a dropped
# realm, credential rows that would not authenticate, and create_catalog 500ing
# with grantee_not_found at 100% -- all had the same root cause: Polaris was not
# restarted after the schema was dropped and re-bootstrapped. InMemoryEntityCache
# holds entities WITH their grants, so a running instance keeps serving a realm
# that no longer exists in the tables.
#
# The restart is easy to forget precisely because the SQL succeeds without it.
# So it is not a step here, it is THE step: this script refuses to report success
# until Polaris has restarted, come back, and answered a token request on 8181.

set -euo pipefail

NS="${POLARIS_K8S_NAMESPACE:-datahub-hynix}"
DEPLOY="${POLARIS_K8S_DEPLOYMENT:-benchmarks-polaris}"
POLARIS_URL="${POLARIS_URL:-http://192.168.139.2:8181}"
ROOT_CLIENT="${POLARIS_ROOT_CLIENT:-root}"
ROOT_SECRET="${POLARIS_ROOT_SECRET:-polaris-secret}"
REALM="${POLARIS_REALM:-POLARIS}"
SCHEMA="${PG_SCHEMA:-polaris_schema}"

HERE="$(cd "$(dirname "$0")" && pwd)"
SEED_USERS=""
[ "${1:-}" = "--seed" ] && SEED_USERS="${2:?--seed needs a user count}"

# psql runs inside the primary pod; the workstation may not have the client.
PGPOD="$(kubectl get pods -n "$NS" -o name | grep -E 'postgresql-[0-9]+$' | head -1)"
PGPOD="${PGPOD#pod/}"
: "${PGPOD:?no postgresql pod found in namespace $NS}"
psql_primary() {
  kubectl exec -n "$NS" "$PGPOD" -- \
    env PGPASSWORD="${PG_PASSWORD:-polaris}" \
    psql -U "${PG_USER:-polaris}" -d "${PG_DB:-polaris}" -X -q -v ON_ERROR_STOP=1 "$@"
}

echo "== 1. DROP + re-bootstrap schema =="
# The bootstrap file recreates the three bootstrap entities and their grants. It
# does NOT create the schema/tables; a full DROP SCHEMA would also need the
# table DDL. So this truncates the data and re-bootstraps, which is what a reset
# between runs actually wants -- a clean realm in the SAME schema.
psql_primary <<SQL
SET search_path TO ${SCHEMA};
TRUNCATE entities, grant_records, principal_authentication_data,
         policy_mapping_record, events;
SQL
psql_primary -f - < "${HERE}/bootstrap.sql"

echo
echo "== 2. RESTART Polaris (the step that keeps getting skipped) =="
kubectl rollout restart "deploy/${DEPLOY}" -n "$NS"
kubectl rollout status  "deploy/${DEPLOY}" -n "$NS" --timeout=300s

echo
echo "== 3. WAIT until 8181 answers a token request =="
# rollout status only means the pods are Ready, which is not the same as Polaris
# having wired its metastore and being able to authenticate. Prove the latter.
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' \
    -X POST "${POLARIS_URL}/api/catalog/v1/oauth/tokens" \
    -H "Polaris-Realm: ${REALM}" \
    -d "grant_type=client_credentials&client_id=${ROOT_CLIENT}&client_secret=${ROOT_SECRET}&scope=PRINCIPAL_ROLE:ALL" \
    2>/dev/null || echo 000)
  if [ "$code" = "200" ]; then echo "  token request 200 after ${i} tries"; break; fi
  [ "$i" = 60 ] && { echo "  Polaris never authenticated (last ${code})"; exit 1; }
  sleep 2
done

echo
echo "== 4. VERIFY the bootstrap (privilege codes, not just row counts) =="
python3 "${HERE}/triage_realm.py"

if [ -n "$SEED_USERS" ]; then
  echo
  echo "== 5. SEED ${SEED_USERS} users =="
  python3 "${HERE}/seed_polaris.py" --users "$SEED_USERS" --no-tables
  python3 "${HERE}/seed_polaris.py" --upgrade-grants --grants-per-role 50
  echo
  echo "  NOTE: no restart needed after SEEDING. Seeding goes through the API,"
  echo "  so Polaris's cache is written the normal way. The restart is only for"
  echo "  writes made BEHIND Polaris's back -- the drop, and SQL clones."
fi

echo
echo "DONE. Clean realm, Polaris restarted and authenticating."
