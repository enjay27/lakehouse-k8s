# RUNBOOK — the commands, in order

Companion to `PLAN-api-index-matrix.md`. Every command runs **on Kade's machine**,
from the repo root unless stated, inside the `.venv`. Claude's shell cannot reach
the cluster.

Cluster names come from `reset_realm.sh` / `capture.sh` defaults:
`NS=datahub-hynix`, `DEPLOY=benchmarks-polaris`,
`PG_STS=benchmarks-postgresql-postgresql-ha-postgresql`. **The primary is `-1`,
not `-0`** — earlier manual resets hit a read-only replica.

---

## 0. Dump, and prove the dump restores

```bash
NS=datahub-hynix
PGPOD=benchmarks-postgresql-postgresql-ha-postgresql-1        # the PRIMARY
STAMP=$(date +%Y%m%d-%H%M%S)

kubectl exec -n $NS $PGPOD -- bash -c \
  "PGPASSWORD=polaris pg_dump -U polaris -Fc -d polaris -f /tmp/polaris-$STAMP.dump"
kubectl cp $NS/$PGPOD:/tmp/polaris-$STAMP.dump ~/polaris-$STAMP.dump
ls -lh ~/polaris-$STAMP.dump
```

**Prove it restores — this step is the point of the dump.**

```bash
kubectl exec -n $NS $PGPOD -- bash -c \
  "PGPASSWORD=polaris createdb -U polaris restoretest && \
   PGPASSWORD=polaris pg_restore -U polaris -d restoretest /tmp/polaris-$STAMP.dump && \
   PGPASSWORD=polaris psql -U polaris -d restoretest -c \
     'SELECT count(*) FROM polaris_schema.grant_records'"
# then drop it
kubectl exec -n $NS $PGPOD -- bash -c \
  "PGPASSWORD=polaris dropdb -U polaris restoretest"
```

Write the restore command down before continuing:

```bash
# RESTORE:  pg_restore -U polaris -d polaris --clean --if-exists ~/polaris-<STAMP>.dump
```

---

## 1. Seed

```bash
cd diagnostics/api-sql-profile

# 1a. which policy `type` does this build accept? Policies are feature-flagged
#     in 1.3 and have seeded as ZERO here before while GET /policies answered 200.
uv run python seed_polaris.py --probe-policy

# 1b. the main fixture (~30k entities, ~52k grant_records). Slow.
uv run python seed_polaris.py --users 1000 \
    --views-per-namespace 5 \
    --generic-tables-per-namespace 5 \
    --policies-per-namespace 2

# 1c. the admin tier — service_admin, ~1,100 grants each
uv run python seed_polaris.py --users 5 --prefix admin --service-admin

# 1d. the authorized tier, if not already present
uv run python seed_polaris.py --users 100 --prefix authz \
    --views-per-namespace 5 --generic-tables-per-namespace 5
```

Then set the shared secret the seeded principals authenticate with (the seeder
discards the credentials `create_principal` returns, so this is the hand-set one
in `principal_authentication_data`):

```bash
export POLARIS_USER_SECRET='<the shared secret>'
```

### 1e. The zero-grant principal — no flag exists for this

`seed_polaris.py` always grants, so this one is created by hand. Its returned
secret is used directly, so no `principal_authentication_data` edit is needed.

```bash
cd "$(git rev-parse --show-toplevel)"
uv run python - <<'PY'
import sys, pathlib
sys.path.insert(0, "src")
from polaris_test_utils import *
from polaris_rest import PolarisREST
init_env("local")
pc = PolarisREST(POLARIS_URL, REALM, token=root_token())
r = pc.create_principal("zerograve_principal");  print("principal:", r.status_code)
body = r.json()
print("CLIENT_ID    :", body.get("credentials", {}).get("clientId") or body)
print("CLIENT_SECRET:", body.get("credentials", {}).get("clientSecret"))
print("role:", pc.create_principal_role("zerograve_principal_role").status_code)
print("assign:", pc.assign_principal_role_to_principal(
    "zerograve_principal", "zerograve_principal_role").status_code)
print("\nGRANT NOTHING. Verify it holds zero:")
PY
```

**Verify it really holds zero** — a principal that accidentally holds grants makes
the unauthorized case a second copy of the authorized one, and the two would look
consistent:

```bash
kubectl exec -n $NS $PGPOD -- env PGPASSWORD=polaris psql -U polaris -d polaris -c "
SELECT count(*) AS grants_held
FROM polaris_schema.grant_records g
JOIN polaris_schema.entities e ON e.id = g.grantee_id
WHERE e.name LIKE 'zerograve%';"
# expect 0, or only the principal-role chain rows
```

Record the measured volume — every figure in the report is relative to it:

```bash
kubectl exec -n $NS $PGPOD -- env PGPASSWORD=polaris psql -U polaris -d polaris -c "
SELECT 'entities' t, count(*) FROM polaris_schema.entities
UNION ALL SELECT 'grant_records', count(*) FROM polaris_schema.grant_records
UNION ALL SELECT 'policy_mapping_record', count(*) FROM polaris_schema.policy_mapping_record
UNION ALL SELECT 'principal_authentication_data', count(*) FROM polaris_schema.principal_authentication_data;"
```

---

## 2. Archive the current matrix as a TRACKED file

`reports/.gitignore` is `*.md` with `!doc-*-latest.md`, so **only
`doc-api-sql-matrix-latest.md` is tracked**. Its timestamped twin is byte-identical
but ignored, and notebook 01 overwrites `-latest` in place.

```bash
cd diagnostics/api-sql-profile/reports
printf '!doc-api-sql-matrix-20260820-172931.md\n' >> .gitignore
git add -f doc-api-sql-matrix-20260820-172931.md .gitignore
git commit -m "Pin the 2026-08-20 root-driven matrix before regenerating -latest"
cd -
```

---

## 3. Build the probe fixture — ONCE, as admin

```bash
cd diagnostics/api-sql-profile
uv run python drive_api_surface.py --setup
# prints the fixture name and records it in runs/api-surface-fixture.json
```

All three cases must drive the **same** fixture, or they differ by more than the
identity and the comparison stops meaning anything.

---

## 4. Three drives — restart Polaris before EACH one

**Order: unauthorized, authorized, admin LAST.** Only the admin drive mutates.

```bash
restart_polaris () {
  kubectl rollout restart deploy/benchmarks-polaris -n datahub-hynix
  # rollout restart only PATCHES the template, so rollout status right after can
  # report the PREVIOUS rollout complete. Wait for the patch to be observed:
  kubectl rollout status deploy/benchmarks-polaris -n datahub-hynix --timeout=300s
  # readiness is 8181 answering a TOKEN, not 8182 /q/health/ready:
  until curl -sf -o /dev/null -X POST http://192.168.139.2:8181/api/catalog/v1/oauth/tokens \
      -d 'grant_type=client_credentials&client_id=root&client_secret=polaris-secret&scope=PRINCIPAL_ROLE:ALL'; do
    sleep 3; echo -n .
  done; echo " polaris up"
}
```

### 4a. unauthorized

```bash
restart_polaris
./capture.sh pgon                                  # rotate alone does NOT do this
./capture.sh rotate capture-unauth-$(date +%H%M%S)
POLARIS_USER_SECRET='<zerograve secret from 1e>' \
uv run python drive_api_surface.py --drive --case unauthorized \
    --client-id '<zerograve clientId>' \
    --principal-role zerograve_principal_role
```

### 4b. authorized

```bash
restart_polaris
./capture.sh rotate capture-authz-$(date +%H%M%S)
uv run python drive_api_surface.py --drive --case authorized
```

### 4c. admin — LAST

```bash
restart_polaris
./capture.sh rotate capture-admin-$(date +%H%M%S)
uv run python drive_api_surface.py --drive --case admin
./capture.sh pgoff
```

Each drive writes `reports/doc-api-sql-matrix-<case>-<stamp>.md` and
`runs/apidrive-<case>-<stamp>.json`.

---

## 5. EXPLAIN — each case, both index states

Dry-run first; it touches no database and prints the worklist:

```bash
uv run python explain_api_matrix.py --case admin --index-state present \
    --matrix reports/doc-api-sql-matrix-admin-<stamp>.md --dry-run
```

Then, index PRESENT (the current state):

```bash
for c in unauthorized authorized admin; do
  uv run python explain_api_matrix.py --case $c --index-state present \
      --matrix reports/doc-api-sql-matrix-$c-<stamp>.md
done
```

Toggle, and take the other half:

```bash
uv run python drop_grantee_index.py
kubectl exec -n $NS $PGPOD -- env PGPASSWORD=polaris psql -U polaris -d polaris \
  -c "ANALYZE polaris_schema.grant_records;"      # NOT optional

for c in unauthorized authorized admin; do
  uv run python explain_api_matrix.py --case $c --index-state absent \
      --matrix reports/doc-api-sql-matrix-$c-<stamp>.md
done

kubectl exec -n $NS $PGPOD -- env PGPASSWORD=polaris psql -U polaris -d polaris -c \
  "CREATE INDEX CONCURRENTLY idx_grant_records_grantee
     ON polaris_schema.grant_records (realm_id, grantee_catalog_id, grantee_id);"
kubectl exec -n $NS $PGPOD -- env PGPASSWORD=polaris psql -U polaris -d polaris \
  -c "ANALYZE polaris_schema.grant_records;"
```

---

## 6. Teardown, and hand back

```bash
uv run python drive_api_surface.py --teardown
git status --short           # six runs/apiexplain-*.json + three reports
```

Then tell Claude, and it writes the combined report and its verifier.

---

## What will refuse you, and why

- `explain_api_matrix.py` **refuses a report that did not fully parse**, before
  touching the database. A short worklist looks exactly like a complete one.
- It **refuses an `--index-state` that disagrees with live `pg_indexes`.** EXPLAIN
  replays against the database as it IS; without the check you get one document
  holding two cluster states.
- `drive_api_surface.py --drive` **refuses without `runs/api-surface-fixture.json`**
  — run `--setup` first.
- `--client-id` **refuses without `--principal-role`.** The only available default
  would be `PRINCIPAL_ROLE:ALL`, which is root's scope: a non-root principal gets
  a 200 and a token with no effective role, and every later 403 becomes a
  statement about a scope string.
- Three of the 115 pairs are **unreplayable for a fixable reason** (`param_tuple`
  splits bound values on `", "`, and JSON property blobs contain it). They are
  reported as refused-with-reason, not planned. Say the word and I fix the
  splitter.
