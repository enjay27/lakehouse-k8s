#!/usr/bin/env bash
# preflight-triage.sh — why did every image report UNAVAILABLE?
# Read-only. Pulls nothing, changes nothing, touches no cluster.
#
#   bash preflight-triage.sh
#
# Purpose: distinguish "the images are genuinely withdrawn" (a real stop)
# from "the pull environment is broken" (fix it and re-run the gate).

echo "############################################################"
echo "# 1. Is the Docker daemon even up?"
echo "############################################################"
if docker info >/dev/null 2>&1; then
    echo "OK: daemon responding"
    docker info --format 'server={{.ServerVersion}} storage={{.Driver}} images={{.Images}}' 2>/dev/null
else
    echo "!! DAEMON NOT RESPONDING — this alone explains every UNAVAILABLE line."
    echo "   OrbStack may be stopped. Start it, then re-run this script."
    docker info 2>&1 | head -5
    exit 1
fi
echo

echo "############################################################"
echo "# 2. CONTROL TEST — a tiny image nobody has withdrawn"
echo "############################################################"
echo "If this fails, the problem is your environment, not the registry."
docker pull alpine:3.19 2>&1 | tail -3
echo

echo "############################################################"
echo "# 3. Registry reachability, WITHOUT pulling layers"
echo "############################################################"
echo "manifest inspect hits the registry API only. Distinct errors:"
echo "  'manifest unknown'  -> genuinely withdrawn      (REAL STOP)"
echo "  'unauthorized'      -> auth / paywall          (login or migrate)"
echo "  'toomanyrequests'   -> Docker Hub rate limit   (wait or log in)"
echo "  DNS / timeout       -> network                 (fix and retry)"
echo
for img in \
  alpine:3.19 \
  apache/polaris:1.3.0-incubating \
  apache/airflow:2.9.1 \
  minio/minio:RELEASE.2024-01-01T16-36-33Z \
  minio/mc:latest \
  jupyter/pyspark-notebook:spark-3.5.0 \
  cr.fluentbit.io/fluent/fluent-bit:3.2.2 \
  bitnamilegacy/postgresql-repmgr:17.6.0-debian-12-r2 \
  bitnamilegacy/pgpool:4.6.3-debian-12-r0 \
  bitnamilegacy/os-shell:12-debian-12-r51 \
  bitnamilegacy/spark:3.5.3 ; do
    printf '%-58s ' "$img"
    out=$(docker manifest inspect "$img" 2>&1)
    if [ $? -eq 0 ]; then
        echo "PRESENT"
    else
        echo "FAIL: $(echo "$out" | head -1 | cut -c1-90)"
    fi
done
echo

echo "############################################################"
echo "# 4. Docker Hub rate limit / auth state"
echo "############################################################"
echo "Anonymous pulls are capped per IP per 6h. Ten multi-layer images"
echo "can exhaust it, and every subsequent pull then looks 'unavailable'."
grep -o '"auths":{[^}]*}' ~/.docker/config.json 2>/dev/null || echo "(no ~/.docker/config.json auths block — pulling anonymously)"
TOKEN=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:ratelimitpreview/test:pull" | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')
if [ -n "$TOKEN" ]; then
    curl -s --head -H "Authorization: Bearer $TOKEN" \
      https://registry-1.docker.io/v2/ratelimitpreview/test/manifests/latest \
      | grep -i 'ratelimit' || echo "(no ratelimit headers returned)"
else
    echo "!! could not obtain an anonymous Hub token — network or DNS problem"
fi
echo

echo "############################################################"
echo "# 5. Disk — a full disk makes pulls fail as if remote"
echo "############################################################"
df -h / 2>/dev/null | tail -1
docker system df 2>/dev/null
echo

echo "############################################################"
echo "# 6. Do the images ALREADY exist locally?"
echo "############################################################"
echo "If they are cached, you can skip the pull entirely and go"
echo "straight to 'docker save' for the tarball."
docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null \
  | grep -E 'polaris|airflow|minio|jupyter|fluent-bit|bitnamilegacy' \
  | sort || echo "(none cached)"
echo

echo "############################################################"
echo "# 7. Helm repos — the reason rebuild-image-list.txt was empty"
echo "############################################################"
helm repo list 2>&1
echo
echo "Expected for a full reinstall: bitnami, datahub, argo,"
echo "apache-airflow, jupyterhub, fluent."
echo
echo "############################################################"
echo "VERDICT GUIDE"
echo "############################################################"
echo "alpine:3.19 FAILED           -> environment. Nothing about the images"
echo "                                is known yet. Fix, re-run, re-gate."
echo "alpine PASSED, all others"
echo "  'manifest unknown'         -> genuine withdrawal. DO NOT RESET."
echo "  'unauthorized'             -> Bitnami paywall and/or Hub login."
echo "                                Non-Bitnami images failing this way"
echo "                                means a login/proxy problem instead."
echo "  'toomanyrequests'          -> rate limit. Wait for the reset window"
echo "                                shown in section 4, or docker login."
echo "Mixed results                -> read per-image. Only bitnamilegacy/*"
echo "                                failing is the scenario HANDOFF §2"
echo "                                actually predicted."
