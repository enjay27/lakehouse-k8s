#!/usr/bin/env bash
# Reset the realm: apply schema + bootstrap on the PRIMARY, RESTART Polaris,
# wait, verify -- one command, restart never skipped.
#
#   ./reset_realm.sh                 # schema + bootstrap + restart + verify
#   ./reset_realm.sh --seed 50       # ...then seed 50 users and upgrade grants
#
# This mirrors Kade's manual flow (2026-08-24): kubectl cp schema.sql and
# bootstrap.sql into the postgresql pod, psql -f both, then restart Polaris.
# It fixes two things about doing it by hand:
#
#   1. RUN ON THE PRIMARY ONLY. Kade ran the DDL on all three postgresql pods
#      "because I don't know which is primary". Only the primary accepts writes;
#      on a streaming replica those psql -f calls error (read-only transaction)
#      or no-op, and the primary's writes replicate to the others anyway. This
#      DETECTS the primary via pg_is_in_recovery() and runs there once.
#
#   2. THE RESTART IS NOT OPTIONAL. Three failures this session -- a stale cache
#      serving a dropped realm, credentials that would not authenticate, and
#      create_catalog 500ing with grantee_not_found at 100% -- were all the same
#      missing restart. The SQL succeeds without it, which is exactly why it gets
#      skipped. So this refuses to report success until Polaris has restarted,
#      come back, and answered a token request on 8181.
#
# The schema/bootstrap files are Kade's, under local-k8s -- the source of truth,
# not the repo's reference copy. Override the paths with SCHEMA_SQL / BOOTSTRAP_SQL.

set -euo pipefail

NS="${POLARIS_K8S_NAMESPACE:-datahub-hynix}"
DEPLOY="${POLARIS_K8S_DEPLOYMENT:-benchmarks-polaris}"
POLARIS_URL="${POLARIS_URL:-http://192.168.139.2:8181}"
ROOT_CLIENT="${POLARIS_ROOT_CLIENT:-root}"
ROOT_SECRET="${POLARIS_ROOT_SECRET:-polaris-secret}"
REALM="${POLARIS_REALM:-POLARIS}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCHEMA_SQL="${SCHEMA_SQL:-$REPO_ROOT/schema/schema.sql}"
BOOTSTRAP_SQL="${BOOTSTRAP_SQL:-$REPO_ROOT/schema/bootstrap.sql}"

PG_USER="${PG_USER:-polaris}"
PG_DB="${PG_DB:-polaris}"
PG_PASSWORD="${PG_PASSWORD:-polaris}"

HERE="$(cd "$(dirname "$0")" && pwd)"
SEED_USERS=""
[ "${1:-}" = "--seed" ] && SEED_USERS="${2:?--seed needs a user count}"

for f in "$SCHEMA_SQL" "$BOOTSTRAP_SQL"; do
  [ -f "$f" ] || { echo "not found: $f (set SCHEMA_SQL / BOOTSTRAP_SQL)"; exit 1; }
done

psql_in() {  # psql_in <pod> [psql args...]
  local pod="$1"; shift
  kubectl exec -n "$NS" "$pod" -- \
    env PGPASSWORD="$PG_PASSWORD" \
    psql -U "$PG_USER" -d "$PG_DB" -X -q "$@"
}

echo "== 0. FIND THE PRIMARY =="
# Ask each postgresql pod whether it is in recovery. The one that says 'f' is
# the primary and the only pod that can take the DDL.
PRIMARY=""
for pod in $(kubectl get pods -n "$NS" -o name | grep -E 'postgresql-[0-9]+$'); do
  pod="${pod#pod/}"
  rec=$(psql_in "$pod" -tA -c "SELECT pg_is_in_recovery()" 2>/dev/null | tr -d '[:space:]')
  echo "  ${pod}: in_recovery=${rec:-?}"
  [ "$rec" = "f" ] && PRIMARY="$pod"
done
: "${PRIMARY:?no primary found -- every postgresql pod reports in_recovery=t, or none answered}"
echo "  -> primary is ${PRIMARY}"

echo
echo "== 1. APPLY schema, TRUNCATE, then bootstrap ON THE PRIMARY =="
# The order matters, and the TRUNCATE is not optional. schema_v3.sql is
# CREATE TABLE IF NOT EXISTS + INSERT ... ON CONFLICT DO UPDATE throughout, so
# on a realm that already has tables it is a NO-OP: it creates nothing and
# clears nothing. Running it does not reset anything.
#
# So the reset comes from the TRUNCATE between schema and bootstrap:
#   - schema first, to CREATE the tables on a genuinely empty database (and
#     do nothing on an existing one);
#   - TRUNCATE, which is THE reset -- it empties every table for every realm;
#   - bootstrap last, into now-empty tables. bootstrap.sql is a plain INSERT
#     with no ON CONFLICT, so without the TRUNCATE it would ERROR on the
#     existing bootstrap rows under ON_ERROR_STOP -- a safety net, but not a
#     reset. TRUNCATE makes the insert clean.
#
# TRUNCATE keeps table structure and indexes (unlike DROP SCHEMA), which is
# what the audit wants -- index state is managed explicitly elsewhere.
#
# schema.sql is applied ONLY when the schema does not yet exist. Kade's real
# schema.sql opens with a bare `CREATE SCHEMA POLARIS_SCHEMA` (no IF NOT
# EXISTS), so on an existing database it errors on line 1 and, under
# ON_ERROR_STOP, aborts before the reset ever happens. On an existing realm the
# tables are already there and schema.sql has nothing to do -- the reset is the
# TRUNCATE. So run schema.sql for first-time creation, skip it otherwise.
kubectl cp "$SCHEMA_SQL"    "$NS/$PRIMARY:/tmp/schema.sql"
kubectl cp "$BOOTSTRAP_SQL" "$NS/$PRIMARY:/tmp/bootstrap.sql"
have_schema=$(psql_in "$PRIMARY" -tA -c \
  "SELECT 1 FROM information_schema.schemata WHERE schema_name = '${PG_SCHEMA:-polaris_schema}'" \
  2>/dev/null | tr -d '[:space:]')
if [ "$have_schema" = "1" ]; then
  echo "  schema exists -- skipping schema.sql (reset is the TRUNCATE below)"
else
  echo "  schema absent -- applying schema.sql to create the tables"
  psql_in "$PRIMARY" -v ON_ERROR_STOP=1 -f /tmp/schema.sql
fi
# TRUNCATE via -c, NOT a heredoc on stdin. `kubectl exec` does not forward
# stdin unless invoked with -i, so a heredoc silently reaches psql as empty
# input: psql runs nothing, exits 0, and bootstrap then hits the un-truncated
# rows with a duplicate-key error. That is exactly what happened on the first
# run. `-c` passes the statement as an argument, independent of stdin. The
# `-f` calls above are unaffected -- psql reads those files inside the pod.
SCH="${PG_SCHEMA:-polaris_schema}"
psql_in "$PRIMARY" -v ON_ERROR_STOP=1 -c \
  "TRUNCATE ${SCH}.entities, ${SCH}.grant_records, \
   ${SCH}.principal_authentication_data, ${SCH}.policy_mapping_record, \
   ${SCH}.events"
psql_in "$PRIMARY" -v ON_ERROR_STOP=1 -f /tmp/bootstrap.sql
echo "  schema ensured, tables truncated, bootstrap applied."
echo "  Replicas will catch up via streaming replication."

echo
echo "== 2. RESTART Polaris (the step that keeps getting skipped) =="
kubectl rollout restart "deploy/${DEPLOY}" -n "$NS"
kubectl rollout status  "deploy/${DEPLOY}" -n "$NS" --timeout=300s

echo
echo "== 3. WAIT until 8181 answers a token request =="
# rollout status only means the pods are Ready, which is not the same as Polaris
# having wired its metastore and being able to authenticate. Prove the latter --
# and prove root's bootstrap grants are right, since a wrong privilege code
# authenticates but 403s on the first write.
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
  echo "  writes made BEHIND Polaris's back -- the schema apply, and SQL clones."
fi

echo
echo "DONE. Clean realm on the primary, Polaris restarted and authenticating."
