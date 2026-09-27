#!/usr/bin/env bash
# step15 — Can N Polaris pods share ONE log file if rotation is size-driven and fast? (#48 follow-up)
#
# Kade, 2026-09-27: "How about one file for all pods? Test it with a small size for rotation."
# The test makes the question countable instead of arguable: every request carries a unique
# ?i=<n>, each request writes exactly one access-log line, so after the run every i in 1..N must
# appear exactly once across the active file and all its rolls. Missing i = lost lines.
#
#   bash logging/scripts/step15-shared-file-size-rotation-test.sh shared    # one file, all pods
#   bash logging/scripts/step15-shared-file-size-rotation-test.sh perpod    # control: file per pod
#   bash logging/scripts/step15-shared-file-size-rotation-test.sh restore   # back to values.yaml
#
# Each mode: helm upgrade with TEMPORARY --set overrides (values.yaml is not edited) —
#   maxFileSize 100k (rolls every ~250 access lines), minReplicas 2 (two writers guaranteed) —
# then N requests from an in-cluster curl pod through the Service (spread over both pods),
# then every test file is copied out with `exec cat` (the image has no tar/zcat) and counted.
# Test files use their own prefix (polaris-sizetest-*) so real logs are never mixed in.
# Run `restore` afterwards: until then the HPA floor is 2 and files roll every 100 kB.
set -euo pipefail
NS=datahub-hynix; REL=benchmarks-polaris; CHART=./charts/polaris; VALUES=charts/polaris/values.yaml
LOGDIR=/deployments/logs; N=${N:-3000}; PY=${PY:-python3}
MODE=${1:?usage: $0 shared|perpod|restore}

ctx=$(kubectl config current-context)
[ "$ctx" = orbstack ] || { echo "context is '$ctx', not orbstack — refusing" >&2; exit 1; }

case "$MODE" in
  shared) NAME='polaris-sizetest-shared.log' ;;
  perpod) NAME='polaris-sizetest-${HOSTNAME}.log' ;;
  restore)
    helm upgrade --install $REL $CHART -f $VALUES -n $NS
    kubectl -n $NS rollout status deploy/$REL --timeout=10m
    kubectl -n $NS exec deploy/$REL -- sh -c "cd $LOGDIR && mkdir -p sizetest && mv polaris-sizetest-* sizetest/ 2>/dev/null; ls -ln sizetest | tail -5"
    exit 0 ;;
  *) echo "unknown mode $MODE" >&2; exit 1 ;;
esac

echo "== archiving files from any earlier test run into $LOGDIR/sizetest/"
kubectl -n $NS exec deploy/$REL -- sh -c "cd $LOGDIR && mkdir -p sizetest && mv polaris-sizetest-* sizetest/ 2>/dev/null; true"

echo "== $MODE: upgrade with fileName=$NAME, maxFileSize=100k, minReplicas=2"
helm upgrade --install $REL $CHART -f $VALUES -n $NS \
  --set-string "logging.file.fileName=$NAME" \
  --set-string logging.file.rotation.maxFileSize=100k \
  --set autoscaling.minReplicas=2
kubectl -n $NS rollout status deploy/$REL --timeout=10m
sleep 20   # let the HPA reach its new floor
kubectl -n $NS get pods -l app.kubernetes.io/instance=$REL

RUN=$(date +%s)
echo "== sending $N requests (run $RUN) through svc/$REL"
kubectl -n $NS run sizetest-$RUN --rm -i --restart=Never --image=curlimages/curl --command -- \
  sh -c "i=1; while [ \$i -le $N ]; do curl -s -o /dev/null http://$REL:8181/api/catalog/v1/config?sizetest=$RUN-\$i; i=\$((i+1)); done; echo sent $N"
sleep 10   # let the last lines flush

OUT=$(mktemp -d /tmp/sizetest-$MODE-XXXX)
echo "== copying test files to $OUT"
for f in $(kubectl -n $NS exec deploy/$REL -- sh -c "cd $LOGDIR && ls polaris-sizetest-* 2>/dev/null"); do
  kubectl -n $NS exec deploy/$REL -- cat "$LOGDIR/$f" > "$OUT/$f"
done
ls -ln "$OUT"

$PY - "$OUT" "$RUN" "$N" <<'PY'
import gzip, json, os, re, sys, collections
out, run, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
pat = re.compile(r"sizetest=" + re.escape(run) + r"-(\d+)")
seen = collections.Counter(); bad = 0
print(f"{'file':70} {'lines':>6} {'ids':>5}  hostNames")
for f in sorted(os.listdir(out)):
    p = os.path.join(out, f)
    try:
        raw = gzip.open(p, "rt").read() if f.endswith(".gz") else open(p).read()
    except Exception as e:
        print(f"{f:70}  UNREADABLE: {e}"); bad += 1; continue
    hosts, ids, lines = set(), 0, 0
    for line in raw.splitlines():
        lines += 1
        try: rec = json.loads(line)
        except ValueError: bad += 1; continue
        hosts.add(rec.get("hostName", "?"))
        m = pat.search(rec.get("message", ""))
        if m: seen[int(m.group(1))] += 1; ids += 1
    print(f"{f:70} {lines:6} {ids:5}  {','.join(sorted(hosts))}")
missing = [i for i in range(1, n + 1) if seen[i] == 0]
dups = sum(1 for c in seen.values() if c > 1)
print(f"\nsent {n} | found {len(seen)} distinct | MISSING {len(missing)} | duplicated {dups} | unparseable lines/files {bad}")
if missing: print("first missing ids:", missing[:20])
if len(seen) == 0: print("NO test lines found — is the access log enabled? check one file by hand.")
print("VERDICT:", "no loss" if not missing and not bad and seen else "LOSS OR CORRUPTION")
PY
echo "== files kept in $OUT; run '$0 restore' when done"
