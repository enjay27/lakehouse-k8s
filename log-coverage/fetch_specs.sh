#!/usr/bin/env bash
# Vendor the Apache Polaris OpenAPI documents at POLARIS_TAG.
#
# THE TAG IS THE POINT, AND IT MUST MATCH THE SERVER.
# On 2026-09-21 this script was run with the tag bumped to 1.6.0 and the
# previous documents were overwritten in place. Nothing recorded the
# change, so run 1789950539 -- driven 19 minutes earlier against 63
# operations and 286 cells -- became unreproducible: the same call now
# answers 65 and 297. Hence the inventory write at the end of this script:
# it is not bookkeeping, it is the only durable statement of what a
# coverage figure was a figure OF.
#
# WHY THIS SCRIPT EXISTS RATHER THAN A LIVE FETCH FROM THE SERVER
# ---------------------------------------------------------------
# Polaris 8181/8182 serves NO OpenAPI document. Measured 2026-08-31: every
# `/q/openapi*` and `/openapi*` candidate came back empty. Two plausible
# reasons -- `quarkus-smallrye-openapi` is not in the server build, or it is
# present but not exposed outside dev mode -- and neither is worth chasing,
# because what these files give is a list of things to go and CHECK, never a
# coverage verdict. A document describes what a build INTENDS to serve.
#
# So these are a statement about a VERSION. `log_coverage.spec_inventory` keeps
# them in their own column, apart from what this deployment has actually been
# observed to serve.
#
# The downloads are gitignored; `spec/inventory.json`, written by the notebook,
# is the durable artifact and records each file's sha256, the operation and
# cell counts it produces, and the fingerprint it superseded.
set -euo pipefail

TAG="${POLARIS_TAG:-apache-polaris-1.6.0}"
DEST="$(cd "$(dirname "$0")" && pwd)/spec"
BASE="https://raw.githubusercontent.com/apache/polaris/${TAG}"

mkdir -p "$DEST"

fetch() {
  local url="$1" out="$2"
  echo "  $out"
  curl -fsSL --retry 2 "$url" -o "$DEST/$out" || {
    echo "  !! could not fetch $url" >&2
    echo "     (no network, or the path moved in this tag -- check the tree at" >&2
    echo "      https://github.com/apache/polaris/tree/${TAG}/spec)" >&2
    return 1
  }
}

echo "vendoring OpenAPI documents at tag ${TAG} into ${DEST}"
fetch "${BASE}/spec/polaris-management-service.yml" "polaris-management-service.yml"

# The Iceberg REST spec is vendored inside the Polaris tree; its filename has
# moved between releases, so try the names this tag is known to use.
for candidate in \
  "spec/rest-catalog-open-api.yaml" \
  "spec/iceberg-rest-catalog-open-api.yaml" \
  "spec/polaris-catalog-service.yaml"
do
  if curl -fsSL --retry 1 "${BASE}/${candidate}" -o "$DEST/rest-catalog-open-api.yaml" 2>/dev/null; then
    echo "  rest-catalog-open-api.yaml   (from ${candidate})"
    break
  fi
done

echo
echo "vendored:"
for f in "$DEST"/*.y*ml; do
  [ -e "$f" ] || { echo "  NOTHING -- the notebook will report the spec column as absent"; break; }
  printf "  %-40s %s\n" "$(basename "$f")" "$(shasum -a 256 "$f" | cut -c1-16)"
done

# RECORD THE DENOMINATOR, or the fetch above is an untraceable overwrite.
# `spec/inventory.json` is the one tracked file in that directory; the previous
# fingerprint is pushed onto its `history` rather than lost.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
echo
python3 - "$REPO" "$DEST" "$TAG" <<'PY'
import sys
repo, dest, tag = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, repo + "/src")
import api_status_matrix as m

rec = m.write_inventory(dest, tag=tag, note=f"log-coverage/fetch_specs.sh at {tag}")
print(
    f"  inventory.json   {rec['operations']} operations, {rec['cells']} cells, "
    f"{len(rec['history'])} superseded fingerprint(s) kept"
)
PY
