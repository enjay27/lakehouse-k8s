#!/usr/bin/env bash
# =============================================================================
# capture.sh — start / stop / rotate the API-SQL trace capture streams   (v2)
# =============================================================================
#   ./capture.sh preflight       check every stream CAN work, change nothing
#   ./capture.sh pgon            turn on PG statement logging on ALL replicas
#   ./capture.sh pgoff           turn it back off
#   ./capture.sh start [dir]     start all streams into <dir> (default ./capture)
#   ./capture.sh stop            stop every stream this script started
#   ./capture.sh status          what is running, where it writes, how big
#   ./capture.sh rotate [dir]    stop, then start again into a NEW dir
#
# Env overrides:
#   NS=datahub-hynix  POLARIS=deploy/benchmarks-polaris
#   MINIO_POD=<pod>  MC_ALIAS=local  BUCKET=data-catalog-bucket
#   PG_STS=benchmarks-postgresql-postgresql-ha-postgresql  PGPASSWORD=...
#   CAPTURE_DIR=/some/path
#
# ---------------------------------------------------------------------------
# WHAT v1 GOT WRONG
# ---------------------------------------------------------------------------
# 1. MinIO: v1/v2 looked for `mc` ON THIS MACHINE. There is none and there
#    never needed to be — the MinIO image ships mc, and the working capture
#    was produced by `kubectl exec <minio-pod> -- mc admin trace`. v3 runs it
#    in the pod, auto-discovering the pod, the binary name and the alias.
#
# 2. PostgreSQL: v2 claimed `kubectl logs` can NEVER show statement logs on
#    Bitnami. That is wrong, and Kade's working one-liner proves it. Bitnami
#    uses `pg_ctl -l $POSTGRESQL_LOG_FILE` only during init/setup; once setup
#    finishes it `exec`s postgres in the FOREGROUND, so on a healthy pod
#    stdout is the container's stdout and `kubectl logs -f` is correct.
#    (The file sink is real, but only for a pod still in — or stuck in — init,
#    which is exactly the case capture_pg_startup_error.sh was written for.
#    I generalised that special case to the steady state.)
#    v4 stops guessing and asks the kernel: readlink /proc/<postmaster>/fd/1.
#    A 0-byte pg.log here was never the stream — it was log_statement='none'.
#
# WHY `--since=1s` MATTERS
#   `kubectl logs -f` replays the pod's ENTIRE retained buffer before it
#   follows. Restarting a capture without it duplicates every line already in
#   the old file, silently inflating per-API statement counts.
# =============================================================================
set -uo pipefail

NS="${NS:-datahub-hynix}"
POLARIS="${POLARIS:-deploy/benchmarks-polaris}"
MC_ALIAS="${MC_ALIAS:-localminio}"
BUCKET="${BUCKET:-data-catalog-bucket}"
PG_STS="${PG_STS:-benchmarks-postgresql-postgresql-ha-postgresql}"
PG_LOG_DEFAULT="/opt/bitnami/postgresql/logs/postgresql.log"

CMD="${1:-status}"
DIR="${2:-${CAPTURE_DIR:-./capture}}"
PIDF=".pids"

RED=$'\033[31m'; YEL=$'\033[33m'; GRN=$'\033[32m'; OFF=$'\033[0m'
ok()   { echo "  ${GRN}[+]${OFF} $*"; }
warn() { echo "  ${YEL}[!]${OFF} $*"; }
bad()  { echo "  ${RED}[x]${OFF} $*"; }

_alive() { kill -0 "$1" 2>/dev/null; }

_human() {
  local f="$1"; [[ -f "$f" ]] || { echo "-"; return; }
  awk -v b="$(wc -c < "$f" | tr -d ' ')" 'BEGIN{
    split("B KB MB GB",u," "); i=1
    while (b>=1024 && i<4) { b/=1024; i++ }
    printf "%.1f%s", b, u[i] }'
}

# --------------------------------------------------------------- discovery ---
# The MinIO client is NOT expected on the host. The Bitnami/MinIO image ships
# `mc` inside the pod, and that is where it runs — `kubectl exec <minio-pod> --
# mc admin trace`. v2 wrongly looked for a host binary and failed preflight on
# a machine that never needed one.
minio_pod() {
  local p
  # Prefer a real label, fall back to a name match.
  for sel in "app.kubernetes.io/name=minio" "app=minio"; do
    p=$(kubectl -n "$NS" get pods -l "$sel" \
          --field-selector=status.phase=Running -o name 2>/dev/null \
        | sed 's|^pod/||' | head -1)
    [[ -n "$p" ]] && { echo "$p"; return 0; }
  done
  p=$(kubectl -n "$NS" get pods -o name 2>/dev/null | sed 's|^pod/||' \
      | grep -i minio | grep -vi "console\|job\|provision" | head -1)
  [[ -n "$p" ]] && { echo "$p"; return 0; }
  return 1
}

# Which mc binary exists inside that pod, and which alias does it have set up?
pod_mc() {
  local pod="$1" c
  for c in mc mcli /usr/bin/mc /opt/bitnami/minio-client/bin/mc; do
    kubectl -n "$NS" exec "$pod" -- sh -c "command -v $c" >/dev/null 2>&1 \
      && { echo "$c"; return 0; }
  done
  return 1
}

pod_mc_alias() {
  local pod="$1" mc="$2" aliases
  aliases=$(kubectl -n "$NS" exec "$pod" -- "$mc" alias ls 2>/dev/null \
            | grep -E "^[a-zA-Z0-9_-]+$" | tr -d '\r')
  # honour an explicit MC_ALIAS if the pod actually has it
  if [[ -n "${MC_ALIAS:-}" ]] && echo "$aliases" | grep -qx "$MC_ALIAS"; then
    echo "$MC_ALIAS"; return 0
  fi
  # otherwise prefer a local one over the baked-in public defaults
  local a
  for a in local myminio minio; do
    echo "$aliases" | grep -qx "$a" && { echo "$a"; return 0; }
  done
  a=$(echo "$aliases" | grep -vxE "play|s3|gcs" | head -1)
  [[ -n "$a" ]] && { echo "$a"; return 0; }
  return 1
}

# List the postgres pods of the HA statefulset.
pg_pods() {
  kubectl -n "$NS" get pods -o name 2>/dev/null \
    | sed 's|^pod/||' | grep -E "^${PG_STS}-[0-9]+$" | sort
}

# Where is the RUNNING postmaster's stdout actually pointing?
#
# Bitnami does both, at different times, which is what made this confusing:
#   * during init/setup the entrypoint runs `pg_ctl -l $POSTGRESQL_LOG_FILE`,
#     so output goes to a file in the container and `kubectl logs` shows only
#     wrapper chatter — this is why capture_pg_startup_error.sh has to exec in
#     to debug a crash-looping pod;
#   * once setup completes it `exec`s postgres in the FOREGROUND, so stdout is
#     the container's stdout and `kubectl logs -f` works fine.
# I previously generalised the first case to the second. It is not a guess we
# need to make — ask the kernel where fd 1 of the live postmaster points.
#
# Echoes "stdout" or an absolute file path. Defaults to stdout when it cannot
# tell, since that is the empirically working case on a healthy pod.
pg_sink() {
  local pod="$1" pid target
  pid=$(kubectl -n "$NS" exec "$pod" -c postgresql -- \
          sh -c 'ps -o pid=,comm= 2>/dev/null | awk "\$2==\"postgres\"{print \$1; exit}"' \
        2>/dev/null | tr -d ' \r')
  if [[ -n "$pid" ]]; then
    target=$(kubectl -n "$NS" exec "$pod" -c postgresql -- \
               sh -c "readlink /proc/$pid/fd/1" 2>/dev/null | tr -d '\r')
    case "$target" in
      pipe:*|socket:*|/dev/stdout|/dev/console|"") echo "stdout"; return 0 ;;
      *.log|*/log/*)                               echo "$target"; return 0 ;;
    esac
  fi
  echo "stdout"
}

# Where does this pod's postgres write its log file (init-phase sink)?
pg_logfile() {
  local pod="$1" p
  for p in "$PG_LOG_DEFAULT" "/bitnami/postgresql/data/log" "/opt/bitnami/postgresql/logs"; do
    if kubectl -n "$NS" exec "$pod" -c postgresql -- sh -c "test -f '$p'" >/dev/null 2>&1; then
      echo "$p"; return 0
    fi
    # directory form (logging_collector = on)
    if kubectl -n "$NS" exec "$pod" -c postgresql -- sh -c "test -d '$p'" >/dev/null 2>&1; then
      local newest
      newest=$(kubectl -n "$NS" exec "$pod" -c postgresql -- \
                 sh -c "ls -1t '$p'/*.log 2>/dev/null | head -1" 2>/dev/null | tr -d '\r')
      [[ -n "$newest" ]] && { echo "$newest"; return 0; }
    fi
  done
  return 1
}

# ---------------------------------------------------------------- preflight ---
do_preflight() {
  local fail=0
  echo "namespace: $NS"
  echo
  echo "POLARIS"
  if kubectl -n "$NS" get "$POLARIS" >/dev/null 2>&1; then
    ok "$POLARIS reachable"
    if kubectl -n "$NS" logs --tail=200 "$POLARIS" 2>/dev/null | grep -q "DatasourceOperations"; then
      ok "DatasourceOperations DEBUG is ON (seen in recent output)"
    else
      # No recent lines is ambiguous: idle cluster, or the logger is pinned.
      # Disambiguate by reading the configured level rather than guessing.
      local pinned
      pinned=$(kubectl -n "$NS" get "$POLARIS" -o json 2>/dev/null \
               | tr ',' '\n' | grep -i "DATASOURCEOPERATIONS" | head -4)
      if [[ -n "$pinned" ]]; then
        echo "$pinned" | sed 's/^/        /'
        if echo "$pinned" | grep -qi "INFO\|WARN\|ERROR"; then
          bad "DatasourceOperations is PINNED above DEBUG — no SQL will ever be logged."
          warn "    Most-specific-wins: a package-level DEBUG cannot override this."
          warn "    Remove it from the noise-suppression block in values.yaml."
          fail=1
        else
          ok "DatasourceOperations configured at DEBUG — no recent traffic, that's all"
        fi
      else
        warn "no DatasourceOperations lines recently and no explicit level set."
        warn "    Most likely just idle. Drive one request and re-run preflight:"
        echo "        curl -s -o /dev/null -X POST \$POLARIS_URL/api/catalog/v1/oauth/tokens \\"
        echo "          -d grant_type=client_credentials -d client_id=root -d client_secret=\$SECRET"
      fi
    fi
  else
    bad "$POLARIS not found in $NS"; fail=1
  fi

  echo
  echo "MINIO"
  local mpod mc alias
  if mpod=$(minio_pod); then
    ok "pod: $mpod"
    if mc=$(pod_mc "$mpod"); then
      ok "in-pod client: $mc"
      if alias=$(pod_mc_alias "$mpod" "$mc"); then
        ok "alias '$alias'"
      else
        bad "no usable alias inside the pod. Set one, then re-run:"
        echo "        kubectl -n $NS exec $mpod -- $mc alias set local \\"
        echo "          http://localhost:9000 \$MINIO_ACCESS_KEY \$MINIO_SECRET_KEY"
        fail=1
      fi
    else
      bad "no mc inside $mpod (tried mc, mcli, /opt/bitnami/minio-client/bin/mc)"; fail=1
    fi
  else
    bad "no MinIO pod found in $NS. Override with MINIO_POD=<pod>."; fail=1
  fi

  echo
  echo "POSTGRES"
  local pods; pods=$(pg_pods)
  if [[ -z "$pods" ]]; then
    bad "no pods matching ${PG_STS}-N in $NS"; fail=1
  else
    for pod in $pods; do
      local sink; sink=$(pg_sink "$pod")
      if [[ "$sink" == "stdout" ]]; then
        ok "$pod -> container stdout (kubectl logs -f)"
      else
        ok "$pod -> in-container file $sink (kubectl exec tail -F)"
      fi
      # Use the same four-source lookup as pgon, not a hardcoded guess.
      local st pw
      pw="${PGPASSWORD:-}"
      [[ -z "$pw" ]] && pw=$(pg_superpass "$pod" 2>/dev/null) || true
      st=$(_psql1 "$pod" "$pw" "select current_setting('log_statement')" \
           | tr -d '\r' | tail -1)
      if [[ "$st" == "all" ]]; then
        ok "$pod log_statement = all"
      else
        warn "$pod log_statement = '${st:-unknown}' — statements will NOT be logged."
        warn "    The cluster rebuild reset this. Re-apply on EVERY replica:"
        echo "        kubectl -n $NS exec $pod -c postgresql -- \\"
        echo "          env PGPASSWORD=\$PGPASSWORD psql -U postgres -c \\"
        echo "          \"ALTER SYSTEM SET log_statement='all'; SELECT pg_reload_conf();\""
      fi
    done
  fi
  echo
  [[ "$fail" == "0" ]] && echo "${GRN}preflight OK${OFF}" || echo "${RED}preflight found blockers (above)${OFF}"
  return "$fail"
}

# -------------------------------------------------------------------- stop ---
do_stop() {
  local stopped=0 pf
  for pf in $(ls -1 ./capture/$PIDF ./capture-*/$PIDF "${DIR}/$PIDF" 2>/dev/null | sort -u); do
    while read -r pid label; do
      [[ -z "${pid:-}" ]] && continue
      _alive "$pid" && { kill "$pid" 2>/dev/null; echo "  stopped $label (pid $pid)"; stopped=$((stopped+1)); }
    done < "$pf"
    rm -f "$pf"
  done
  local pat
  for pat in "kubectl.*-n $NS.*logs.*-f" "kubectl.*-n $NS.*exec.*tail -F" "admin trace"; do
    for pid in $(pgrep -f "$pat" 2>/dev/null); do
      _alive "$pid" && { kill "$pid" 2>/dev/null; echo "  stopped stray '$pat' (pid $pid)"; stopped=$((stopped+1)); }
    done
  done
  sleep 1
  for pat in "kubectl.*-n $NS.*logs.*-f" "kubectl.*-n $NS.*exec.*tail -F" "admin trace"; do
    for pid in $(pgrep -f "$pat" 2>/dev/null); do
      _alive "$pid" && kill -9 "$pid" 2>/dev/null && echo "  SIGKILL $pid"
    done
  done
  [[ "$stopped" == "0" ]] && echo "  nothing was running"
  return 0
}

# ------------------------------------------------------------------- start ---
do_start() {
  mkdir -p "$DIR" || { bad "cannot create $DIR"; exit 1; }

  # Captures hold raw request logs and MinIO traces -- never committable, and a
  # rotate into a NEW directory would otherwise arrive untracked-but-unignored.
  # `!.gitignore` matters: a bare `*` also ignores this file, so the rule never
  # reaches anyone who clones the repo.
  if [[ ! -f "$DIR/.gitignore" ]]; then
    printf '%s\n' '*' '!.gitignore' > "$DIR/.gitignore"
    ok "wrote $DIR/.gitignore (ignores everything but itself)"
  fi

  local pf="$DIR/$PIDF"
  if [[ -f "$pf" ]]; then
    while read -r pid label; do
      _alive "${pid:-x}" && { bad "already running: $label (pid $pid)"; echo "  run 'stop' or 'rotate'"; exit 1; }
    done < "$pf"
  fi
  : > "$pf"
  echo "capture dir: $(cd "$DIR" && pwd)"
  local fail=0

  # -- Polaris -----------------------------------------------------------
  if kubectl -n "$NS" get "$POLARIS" >/dev/null 2>&1; then
    kubectl -n "$NS" logs -f --since=1s "$POLARIS" > "$DIR/polaris.log" 2>"$DIR/polaris.err" &
    echo "$! polaris" >> "$pf"; ok "polaris  -> $DIR/polaris.log"
  else
    bad "polaris  FAILED: $POLARIS not found in $NS"; fail=1
  fi

  # -- MinIO -------------------------------------------------------------
  # mc lives INSIDE the pod, not on this machine.
  local mpod mc alias
  mpod="${MINIO_POD:-$(minio_pod)}"
  if [[ -n "$mpod" ]] && mc=$(pod_mc "$mpod") && alias=$(pod_mc_alias "$mpod" "$mc"); then
    kubectl -n "$NS" exec "$mpod" -- \
        "$mc" admin trace --json --path "/$BUCKET/*" "$alias" \
        > "$DIR/minio.json" 2>"$DIR/minio.err" &
    local mpid=$!; echo "$mpid minio" >> "$pf"
    sleep 2
    if _alive "$mpid"; then
      ok "minio    -> $DIR/minio.json   ($mpod: $mc trace $alias)"
    else
      bad "minio    FAILED — died immediately:"
      sed 's/^/        /' "$DIR/minio.err" | head -5; fail=1
    fi
  else
    bad "minio    FAILED: run './capture.sh preflight' for the specific reason."; fail=1
  fi

  # -- PostgreSQL --------------------------------------------------------
  # NOT `kubectl logs` — see the header. Tail the in-container file instead.
  local pods; pods=$(pg_pods)
  if [[ -z "$pods" ]]; then
    bad "postgres FAILED: no pods matching ${PG_STS}-N"; fail=1
  else
    local n=0
    for pod in $pods; do
      local sink idx="${pod##*-}"
      sink=$(pg_sink "$pod")
      if [[ "$sink" == "stdout" ]]; then
        # Normal running pod: postgres is in the foreground, kubectl logs works.
        # One file per replica rather than one shared append target, so a
        # statement can be attributed to the node that ran it.
        kubectl -n "$NS" logs -f --since=1s "$pod" -c postgresql \
            > "$DIR/pg-$idx.log" 2>"$DIR/pg-$idx.err" &
        ok "postgres -> $DIR/pg-$idx.log   ($pod, stdout)"
      else
        kubectl -n "$NS" exec "$pod" -c postgresql -- tail -F -n0 "$sink" \
            > "$DIR/pg-$idx.log" 2>"$DIR/pg-$idx.err" &
        ok "postgres -> $DIR/pg-$idx.log   ($pod, file: $sink)"
      fi
      echo "$! postgres-$idx" >> "$pf"
      n=$((n+1))
    done
    [[ "$n" -gt 0 ]] && warn "if these stay empty it is log_statement, not the stream — './capture.sh preflight'"
  fi

  sleep 3; echo; do_status
  echo
  echo "After driving traffic, verify each stream:"
  echo "  grep -c DatasourceOperations $DIR/polaris.log   # > 0"
  echo "  wc -l $DIR/minio.json $DIR/pg-*.log             # > 0"
  return "$fail"
}

# ------------------------------------------------------------------ status ---
do_status() {
  local found=0 pf
  for pf in $(ls -1 ./capture/$PIDF ./capture-*/$PIDF "${DIR}/$PIDF" 2>/dev/null | sort -u); do
    local d; d=$(dirname "$pf")
    while read -r pid label; do
      [[ -z "${pid:-}" ]] && continue
      local state="DEAD"; _alive "$pid" && state="running"
      local f
      case "$label" in
        polaris)     f="$d/polaris.log" ;;
        minio)       f="$d/minio.json"  ;;
        postgres-*)  f="$d/pg-${label##*-}.log" ;;
        *)           f="$d/$label" ;;
      esac
      printf "  %-12s %-8s pid %-7s %-8s %s\n" "$label" "$state" "$pid" "$(_human "$f")" "$f"
      # surface the reason a dead or silent stream failed
      local ef="${f%.*}.err"; [[ "$label" == minio ]] && ef="$d/minio.err"
      if [[ -s "$ef" && ( "$state" == "DEAD" || "$(_human "$f")" == "0.0B" ) ]]; then
        sed 's/^/                 ! /' "$ef" | head -3
      fi
      found=1
    done < "$pf"
  done
  [[ "$found" == "0" ]] && echo "  no tracked capture streams"
  local stray; stray=$(pgrep -af "kubectl.*logs.*-f|admin trace" 2>/dev/null | grep -v capture.sh || true)
  [[ -n "$stray" ]] && { echo; echo "  untracked streams (started outside this script):"; echo "$stray" | sed 's/^/    /'; }
  return 0
}

# ----------------------------------------------------------- pg superuser ---
# Bitnami keeps TWO passwords: the app user's (POSTGRESQL_PASSWORD -- what is in
# the Polaris JDBC URL) and the superuser's. ALTER SYSTEM needs the superuser.
#
# v4 only read POSTGRESQL_POSTGRES_PASSWORD from the pod env and gave up when it
# was empty. On a chart using an existing/mounted secret the value is NOT in the
# environment at all -- Bitnami exports POSTGRESQL_POSTGRES_PASSWORD_FILE and
# mounts the value as a file. So the lookup now walks four sources, cheapest
# first, and reports what it actually found instead of a dead end.
#
# 0. no password at all: psql over the container's unix socket, which Bitnami's
#    pg_hba usually trusts for local connections. If this works nothing else is
#    needed.
# 1. the plain env vars.
# 2. any *_PASSWORD_FILE env var -> read that file inside the pod.
# 3. the Kubernetes secret, auto-discovered by looking for a key named
#    postgres-password rather than guessing the secret's name.
PG_NOPASS=""          # set to 1 by pg_superpass when socket auth works

pg_superpass() {
  local pod="$1" p f secret

  # 0 -- socket trust
  if kubectl -n "$NS" exec "$pod" -c postgresql -- \
       psql -U postgres -Atc "select 1" >/dev/null 2>&1; then
    PG_NOPASS=1
    echo ""
    return 0
  fi
  PG_NOPASS=""

  # 1 -- plain env
  for v in POSTGRESQL_POSTGRES_PASSWORD POSTGRES_POSTGRES_PASSWORD POSTGRES_PASSWORD; do
    p=$(kubectl -n "$NS" exec "$pod" -c postgresql -- \
          sh -c "printf %s \"\$$v\"" 2>/dev/null | tr -d '\r')
    [[ -n "$p" ]] && { echo "$p"; return 0; }
  done

  # 2 -- *_PASSWORD_FILE env -> read the mounted file
  for v in POSTGRESQL_POSTGRES_PASSWORD_FILE POSTGRES_POSTGRES_PASSWORD_FILE \
           POSTGRES_PASSWORD_FILE; do
    f=$(kubectl -n "$NS" exec "$pod" -c postgresql -- \
          sh -c "printf %s \"\$$v\"" 2>/dev/null | tr -d '\r')
    [[ -z "$f" ]] && continue
    p=$(kubectl -n "$NS" exec "$pod" -c postgresql -- \
          sh -c "cat '$f' 2>/dev/null" 2>/dev/null | tr -d '\r\n')
    [[ -n "$p" ]] && { echo "$p"; return 0; }
  done

  # 2b -- the conventional mount point, even if no env var points at it
  for f in /opt/bitnami/postgresql/secrets/postgres-password \
           /opt/bitnami/postgresql/secrets/postgresql-postgres-password; do
    p=$(kubectl -n "$NS" exec "$pod" -c postgresql -- \
          sh -c "cat '$f' 2>/dev/null" 2>/dev/null | tr -d '\r\n')
    [[ -n "$p" ]] && { echo "$p"; return 0; }
  done

  # 3 -- the secret itself, found by KEY not by guessed name
  secret=$(kubectl -n "$NS" get secret -o \
    'jsonpath={range .items[*]}{.metadata.name}{" "}{.data.postgres-password}{"\n"}{end}' \
    2>/dev/null | awk 'NF==2 {print $1; exit}')
  if [[ -n "$secret" ]]; then
    p=$(kubectl -n "$NS" get secret "$secret" \
          -o jsonpath='{.data.postgres-password}' 2>/dev/null | base64 -d 2>/dev/null)
    [[ -n "$p" ]] && { echo "$p"; return 0; }
  fi
  return 1
}

# Print what IS available, so a failure is actionable rather than a dead end.
pg_password_debug() {
  local pod="$1"
  echo "        password-bearing env vars in $pod:"
  kubectl -n "$NS" exec "$pod" -c postgresql -- \
    sh -c 'env | grep -i pass | sed "s/=.*/=<redacted>/"' 2>/dev/null \
    | sed 's/^/          /' || echo "          <none readable>"
  echo "        secrets in $NS carrying a postgres-password key:"
  kubectl -n "$NS" get secret -o \
    'jsonpath={range .items[*]}{.metadata.name}{" "}{.data.postgres-password}{"\n"}{end}' \
    2>/dev/null | awk 'NF==2 {print "          " $1}' || true
}

# Run ONE statement. Each psql -c is its own implicit transaction.
_psql1() {
  local pod="$1" pw="$2" sql="$3"
  if [[ -z "$pw" ]]; then
    # socket-trust path: passing an empty PGPASSWORD would force a password
    # prompt on some builds, so omit the variable entirely.
    kubectl -n "$NS" exec "$pod" -c postgresql -- \
      psql -U postgres -v ON_ERROR_STOP=1 -Atc "$sql" 2>&1
  else
    kubectl -n "$NS" exec "$pod" -c postgresql -- \
      env PGPASSWORD="$pw" psql -U postgres -v ON_ERROR_STOP=1 -Atc "$sql" 2>&1
  fi
}

# -------------------------------------------------------------------- pgon ---
# Turn statement logging on across ALL replicas. Separate command, never run
# by start — this changes server config and is deliberately explicit.
#   ./capture.sh pgon                 (password read from the pod)
#   PGDUR=1 ./capture.sh pgon         (also per-statement durations)
#   PGPASSWORD=... ./capture.sh pgon  (override the auto-detected superuser pw)
#
# NOTE: each setting is applied with its own `psql -c`. Bundling them into one
# -c makes psql send them as a single simple-query message, which PostgreSQL
# runs in an implicit transaction — and ALTER SYSTEM is rejected inside a
# transaction block. That, not the password, was the original failure.
do_pgon() {
  local stmts=("ALTER SYSTEM SET log_statement='all'")
  if [[ -n "${PGDUR:-}" ]]; then
    stmts+=("ALTER SYSTEM SET log_min_duration_statement=0")
    warn "PGDUR set — every statement logged WITH its duration. Chatty on a"
    warn "    local cluster; run 'pgoff' when the capture is done."
  fi
  stmts+=("SELECT pg_reload_conf()")
  _pgapply "${stmts[@]}"
}

do_pgoff() {
  _pgapply "ALTER SYSTEM SET log_statement='none'" \
           "ALTER SYSTEM SET log_min_duration_statement=-1" \
           "SELECT pg_reload_conf()"
}

_pgapply() {
  local stmts=("$@") pods pw out rc=0
  pods=$(pg_pods)
  [[ -z "$pods" ]] && { bad "no pods matching ${PG_STS}-N in $NS"; return 1; }

  for pod in $pods; do
    # Prefer an explicit override, else the pod's own superuser password.
    pw="${PGPASSWORD:-}"
    if [[ -z "$pw" ]]; then
      if ! pw=$(pg_superpass "$pod"); then
        bad "$pod: no usable superuser credential found."
        echo "        Tried: socket trust, env vars, *_PASSWORD_FILE mounts, and"
        echo "        every secret in $NS carrying a postgres-password key."
        pg_password_debug "$pod"
        echo "        Then re-run as:  PGPASSWORD=<value> ./capture.sh pgon"
        rc=1; continue
      fi
      [[ -z "$pw" ]] && ok "$pod: using socket trust (no password needed)"
    fi

    local podfail=0
    for s in "${stmts[@]}"; do
      out=$(_psql1 "$pod" "$pw" "$s")
      if [[ $? -ne 0 ]]; then
        bad "$pod: $s"
        echo "$out" | sed 's/^/        /' | head -4
        if echo "$out" | grep -qi "password authentication failed"; then
          echo "        ^ this is the SUPERUSER password, not the Polaris app-user one."
          echo "          Bitnami stores them separately (postgres-password vs password)."
        fi
        podfail=1; rc=1; break
      fi
    done

    if [[ "$podfail" == "0" ]]; then
      local now
      now=$(_psql1 "$pod" "$pw" "select current_setting('log_statement')||' / '||current_setting('log_min_duration_statement')")
      ok "$pod  log_statement/min_duration = $now"
    fi
  done
  echo; echo "Verify:  ./capture.sh preflight"
  return "$rc"
}

case "$CMD" in
  preflight) do_preflight ;;
  pgon)      do_pgon ;;
  pgoff)     do_pgoff ;;
  start)     do_start ;;
  stop)      echo "stopping capture streams"; do_stop ;;
  status)    do_status ;;
  rotate)    echo "stopping capture streams"; do_stop; echo; do_start ;;
  *) sed -n '3,12p' "$0"; exit 1 ;;
esac
