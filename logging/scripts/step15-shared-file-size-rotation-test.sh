#!/usr/bin/env bash
# step15 — Can N Polaris pods share ONE log file with fast size rotation? (#48 follow-up)
#
# Kade, 2026-09-27: "one file for all pods, test it with a small size for rotation", and then:
# drive it with the real traffic test, diagnostics/ladders/log-coverage/polaris_api_traffic_v1.ipynb.
#
# THE CHECK. The traffic (same grid as that notebook) tags every call with its own Polaris-Request-Id (`nb-<run>-<seq>-<label>`)
# and its section 13 prints `TOTAL` and says the log "must hold EXACTLY <TOTAL> access lines from this
# run, one per id". Polaris puts that id in `mdc.requestId` of the access line. So after the run, across
# the active test file(s) and every roll, each issued id must appear on exactly ONE access line.
# A second, synthetic load (tagged ?sizetest=<load>-<i>) keeps BOTH pods writing and rolling while the
# traffic runs — its keep-alive sessions alone may all land on one pod.
#
#   step15 run shared           ONE COMMAND: configure, start the load, drive the traffic, verify
#   step15 run perpod           the same, the control
#   step15 restore              back to values.yaml, test files archived to sizetest/
#
# The traffic is diagnostics/ladders/log-coverage/run_traffic.py --profile full: the SAME grid as
# polaris_api_traffic_v1.ipynb (make_traffic.drive, one Polaris-Request-Id per call), without the
# notebook, and it writes traffic-<RUN>.json whose calls[].request_id is the exact issued list.
# It needs src/config/local.yaml (init_env "local") and uv, i.e. run this from the repo root on the Mac.
#
# The pieces, if a step has to be re-run by hand:
#   step15 shared | perpod                      configure + precheck only
#   step15 load                                 start the background load pod, prints <load>
#   step15 verify <RUN> <traffic-RUN.json | ids-file | TOTAL> [<load>]
#
# Overrides (values.yaml is NOT edited): maxFileSize $SIZE (default 50k), maxBackupIndex 5000 (the
# second version's control lost 1929/3000 because 50 deleted the oldest rolls), minReplicas 2, and a
# polaris-sizetest-* file name so real logs are never mixed in. `rollout restart` is required: the chart
# has no config-checksum annotation, so an upgrade that only changes the ConfigMap rolls no pod (the
# first version's runs never reached the test config).
set -euo pipefail
NS=datahub-hynix; REL=benchmarks-polaris; CHART=./charts/polaris; VALUES=charts/polaris/values.yaml
LOGDIR=/deployments/logs; SIZE=${SIZE:-50k}; PY=${PY:-python3}
LOAD_N=${LOAD_N:-4000}; LOAD_SLEEP=${LOAD_SLEEP:-0.05}
MODE=${1:?usage: $0 run shared|perpod | restore | shared|perpod|load|verify}
PYRUN=${PYRUN:-uv run python}

ctx=$(kubectl config current-context)
[ "$ctx" = orbstack ] || { echo "context is '$ctx', not orbstack — refusing" >&2; exit 1; }

configure() {   # $1 = file name (may contain the literal ${HOSTNAME})
  echo "== archiving files from earlier test runs into $LOGDIR/sizetest/"
  kubectl -n $NS exec deploy/$REL -- sh -c "cd $LOGDIR && mkdir -p sizetest && mv polaris-sizetest-* sizetest/ 2>/dev/null; true"
  echo "== upgrade: fileName=$1 maxFileSize=$SIZE maxBackupIndex=5000 minReplicas=2"
  helm upgrade --install $REL $CHART -f $VALUES -n $NS \
    --set-string "logging.file.fileName=$1" \
    --set-string "logging.file.rotation.maxFileSize=$SIZE" \
    --set logging.file.rotation.maxBackupIndex=5000 \
    --set autoscaling.minReplicas=2
  kubectl -n $NS rollout restart deploy/$REL
  kubectl -n $NS rollout status deploy/$REL --timeout=10m
  sleep 20
  echo "== precheck: every running pod must be on the test path, and there must be 2"
  local pods n=0 pod got
  pods=$(kubectl -n $NS get pods -l app.kubernetes.io/instance=$REL \
           --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}')
  for pod in $pods; do
    n=$((n+1))
    got=$(kubectl -n $NS exec "$pod" -- sh -c "grep -o 'quarkus.log.file.path=.*' /deployments/config/application.properties")
    echo "   $pod  $got"
    case "$got" in *polaris-sizetest-*) ;; *) echo "   NOT on the test config — stop" >&2; exit 1 ;; esac
  done
  [ "$n" -ge 2 ] || { echo "only $n pod(s) running — the test needs two writers" >&2; exit 1; }
  kubectl -n $NS exec deploy/$REL -- sh -c "cd $LOGDIR && ls -ln polaris-sizetest-*"
  echo "== ready."
}

start_load() {   # sets LOAD
  LOAD=$(date +%s)
  kubectl -n $NS run sizetest-load-$LOAD --restart=Never --image=curlimages/curl --command -- \
    sh -c "i=1; while [ \$i -le $LOAD_N ]; do curl -s -o /dev/null http://$REL:8181/api/catalog/v1/config?sizetest=$LOAD-\$i; i=\$((i+1)); sleep $LOAD_SLEEP; done; echo sent $LOAD_N"
  kubectl -n $NS wait --for=condition=Ready pod/sizetest-load-$LOAD --timeout=3m || true
  echo "== load $LOAD started: $LOAD_N requests, ${LOAD_SLEEP}s apart, a new connection each (spreads over pods)"
}

do_verify() {   # $1 RUN, $2 traffic json | ids file | TOTAL, $3 load (optional)
  local RUN=$1 ISSUED=$2 LOAD=${3:-} OUT f
  if [ -n "$LOAD" ]; then
    echo "== waiting for load pod sizetest-load-$LOAD to finish"
    kubectl -n $NS wait --for=jsonpath='{.status.phase}'=Succeeded pod/sizetest-load-$LOAD --timeout=30m
    kubectl -n $NS delete pod sizetest-load-$LOAD --wait=false
  fi
  sleep 5
  OUT=$(mktemp -d /tmp/sizetest-verify-XXXX)
  echo "== copying polaris-sizetest-* to $OUT (exec cat: the image has no tar/zcat)"
  for f in $(kubectl -n $NS exec deploy/$REL -- sh -c "cd $LOGDIR && ls polaris-sizetest-* 2>/dev/null"); do
    kubectl -n $NS exec deploy/$REL -- cat "$LOGDIR/$f" > "$OUT/$f"
  done
  $PY - "$OUT" "$RUN" "$ISSUED" "$LOAD" "$LOAD_N" <<'PY'
import collections, gzip, json, os, re, sys
out, run, issued, load, load_n = sys.argv[1:6]
ACCESS = "io.quarkus.http.access-log"
nb = collections.Counter(); ld = collections.Counter(); bad = []
seen_at = collections.defaultdict(list)   # rid -> [(host, timestamp, message)]
top = collections.defaultdict(int)
print(f"{'file':66} {'lines':>6} {'drive':>5} {'load':>5}  hostNames")
for f in sorted(os.listdir(out)):
    p = os.path.join(out, f)
    m = re.match(r"(.+?\.log)\.\d{4}-\d{2}-\d{2}-\d{2}\.(\d+)\.gz$", f)
    if m: top[m.group(1)] = max(top[m.group(1)], int(m.group(2)))
    try:
        raw = gzip.open(p, "rt").read() if f.endswith(".gz") else open(p).read()
    except Exception as e:
        bad.append(f"{f}: {e}"); print(f"{f:66}  UNREADABLE {e}"); continue
    hosts = set(); lines = a = b = 0
    for line in raw.splitlines():
        lines += 1
        try: rec = json.loads(line)
        except ValueError: bad.append(f"{f}: unparseable line {lines}"); continue
        hosts.add(rec.get("hostName", "?"))
        if rec.get("loggerName") != ACCESS: continue
        rid = (rec.get("mdc") or {}).get("requestId") or ""
        if rid.startswith(f"nb-{run}-"):
            nb[rid] += 1; a += 1
            seen_at[rid].append((rec.get("hostName", "?"), rec.get("timestamp", "?"), rec.get("message", "")[:90]))
        if load:
            mm = re.search(r"sizetest=" + re.escape(load) + r"-(\d+)", rec.get("message", ""))
            if mm: ld[int(mm.group(1))] += 1; b += 1
    print(f"{f:66} {lines:6} {a:5} {b:5}  {','.join(sorted(hosts))}")
valid = True
for base, t in sorted(top.items()):
    flag = t >= 4999
    valid &= not flag
    print(f"highest roll index {base}: .{t}" + ("   <-- AT maxBackupIndex: rolls were deleted, INVALID" if flag else ""))
dups = {k: v for k, v in nb.items() if v > 1}
# A duplicated id is only log corruption if the SAME line appears twice. Two different requests
# under one id is the traffic harness reusing it (grant_privilege's skip_if_present GET + PUT, its
# 404 retry on PG-HA lag -- polaris_rest.py), which says nothing about rotation.
true_dups = {k: v for k, v in dups.items() if len(set(seen_at[k])) < len(seen_at[k])}
for k in sorted(dups):
    kind = "SAME LINE TWICE (log duplication)" if k in true_dups else "different requests, one id (harness reuse)"
    print(f"   dup {k}: {kind}")
    for h, ts, m in seen_at[k]: print(f"        {h}  {ts}  {m}")
if os.path.isfile(issued):
    if issued.endswith(".json"):   # run_traffic.py's traffic-<RUN>.json: calls[].request_id
        ids = [c["request_id"] for c in json.load(open(issued)).get("calls", []) if c.get("request_id")]
    else:
        ids = [l.strip() for l in open(issued) if l.strip()]
    missing = [i for i in ids if nb[i] == 0]
    foreign = [k for k in nb if k not in set(ids)]
    print(f"\ntraffic {run}: issued {len(ids)} | found {len(nb)} | MISSING {len(missing)} | duplicated {len(dups)} | not in issued list {len(foreign)}")
    for i in missing[:25]: print("   missing", i)
    for k in foreign[:10]: print("   not issued", k, seen_at[k][0])
    nb_ok = not missing and not true_dups
else:
    total = int(issued)
    print(f"\ntraffic {run}: TOTAL {total} | found {len(nb)} distinct | duplicated {len(dups)}"
          + ("" if len(nb) == total else f"   <-- {total - len(nb):+d} vs TOTAL"))
    print("   (setup calls before section 3b may also carry nb-<run>- ids; an ids-file settles it)")
    nb_ok = len(nb) >= total and not true_dups
if load:
    n = int(load_n); lmiss = [i for i in range(1, n + 1) if ld[i] == 0]
    ldup = sum(1 for v in ld.values() if v > 1)
    print(f"load {load}: sent {n} | found {len(ld)} | MISSING {len(lmiss)} | duplicated {ldup}")
    if lmiss: print("   first missing:", lmiss[:20])
    load_ok = not lmiss and not ldup
else:
    load_ok = True
for x in bad[:10]: print("   BAD", x)
if not nb: print("NO traffic access lines found — wrong RUN, or the traffic hit pods not on the test config?")
print("VERDICT:", "INVALID TEST" if not valid else ("no loss" if nb and nb_ok and load_ok and not bad else "LOSS OR CORRUPTION"))
PY
  echo "== files kept in $OUT"
}

case "$MODE" in
  shared) configure 'polaris-sizetest-shared.log' ;;
  perpod) configure 'polaris-sizetest-${HOSTNAME}.log' ;;
  load)   start_load; echo "   verify with:  $0 verify <RUN> <traffic json|ids-file|TOTAL> $LOAD" ;;
  verify) do_verify "${2:?RUN}" "${3:?traffic json, ids file or TOTAL}" "${4:-}" ;;

  run)
    WHICH=${2:?usage: $0 run shared|perpod}
    case "$WHICH" in
      shared) configure 'polaris-sizetest-shared.log' ;;
      perpod) configure 'polaris-sizetest-${HOSTNAME}.log' ;;
      *) echo "run shared|perpod" >&2; exit 1 ;;
    esac
    start_load
    RUN=$(date +%s); TD=$(mktemp -d /tmp/sizetest-traffic-XXXX)
    echo "== driving run_traffic.py --profile full --run $RUN (mutates: catalog, principals, roles, ns, table, view)"
    $PYRUN diagnostics/ladders/log-coverage/run_traffic.py --env local --profile full --run "$RUN" --runs-dir "$TD"
    [ -f "$TD/traffic-$RUN.json" ] || { echo "no $TD/traffic-$RUN.json — traffic did not complete" >&2; exit 1; }
    echo "== verifying $WHICH"
    do_verify "$RUN" "$TD/traffic-$RUN.json" "$LOAD"
    echo "== $WHICH done. Next: $0 run perpod (if this was shared), then $0 restore"
    ;;

  restore)
    helm upgrade --install $REL $CHART -f $VALUES -n $NS
    kubectl -n $NS rollout restart deploy/$REL
    kubectl -n $NS rollout status deploy/$REL --timeout=10m
    kubectl -n $NS exec deploy/$REL -- sh -c "cd $LOGDIR && mkdir -p sizetest && mv polaris-sizetest-* sizetest/ 2>/dev/null; ls -ln sizetest | tail -5"
    kubectl -n $NS get pods -l run --no-headers 2>/dev/null | awk '/sizetest-load/ {print $1}' | xargs -r kubectl -n $NS delete pod --wait=false
    ;;

  *) echo "unknown mode $MODE" >&2; exit 1 ;;
esac
