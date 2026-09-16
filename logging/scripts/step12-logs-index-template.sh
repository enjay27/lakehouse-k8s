#!/usr/bin/env bash
# ============================================================================
# Apply the polaris-logs-* (detail) index template, and prove it took -- every
# declared field, stored and simulated, compared with the file.
# TODO 1.2/1.3 of logging/PLAN-audit-log-todo-2026-09-16.md. Sibling of step9.
#
#   export OS_URL=https://192.168.194.1:9200 OS_USER=admin OS_PASSWORD='...'
#   bash logging/scripts/step12-logs-index-template.sh            # show current, then apply
#   bash logging/scripts/step12-logs-index-template.sh --dry-run  # show current mappings only
#
# Order is free here (unlike step9): the Lua has written these fields with these
# types since v3, so no in-flight document can be rejected by the template.
# NOT RETROACTIVE -- the first index it shapes is tomorrow's.
# ============================================================================
set -uo pipefail
: "${OS_URL:?}"; : "${OS_USER:?}"; : "${OS_PASSWORD:?}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL="${HERE}/opensearch/polaris-logs-template.json"
OS=(curl -sS -k --max-time 30 -u "${OS_USER}:${OS_PASSWORD}" -H 'Content-Type: application/json')

FLAT=$(python3 -c '
import json,sys
def flat(p, pre=""):
    for k, v in p.items():
        if "properties" in v: yield from flat(v["properties"], pre + k + ".")
        else: yield pre + k
print(",".join(flat(json.load(open(sys.argv[1]))["template"]["mappings"]["properties"])))' "$TPL")

echo "== BEFORE: how the existing polaris-logs-* indices map the declared fields =="
echo "   (a type here that differs from the template is not a fault -- it is what the template prevents next time)"
"${OS[@]}" "${OS_URL}/polaris-logs-*/_mapping/field/${FLAT}" | python3 -c '
import json, sys
data = json.load(sys.stdin)
if not isinstance(data, dict) or "error" in data:
    print("  could not read mappings:", str(data)[:300]); sys.exit(0)
for idx, body in sorted(data.items()):
    got = {f: next(iter(m["mapping"].values()), {}).get("type") for f, m in body.get("mappings", {}).items()}
    print(f"  {idx:<26} " + "  ".join(f"{f}={t}" for f, t in sorted(got.items())))'

[ "${1:-}" = "--dry-run" ] && { echo; echo "dry run: template NOT applied."; exit 0; }

echo
echo "== PUT _index_template/polaris-logs =="
"${OS[@]}" -X PUT "${OS_URL}/_index_template/polaris-logs" --data-binary "@${TPL}"; echo

echo
echo "== read back + simulate, every declared field compared with the file =="
TPL_JSON=$("${OS[@]}" "${OS_URL}/_index_template/polaris-logs")
SIM_JSON=$("${OS[@]}" -X POST "${OS_URL}/_index_template/_simulate_index/polaris-logs-9999.12.31")
python3 - "$TPL" "$TPL_JSON" "$SIM_JSON" <<'PY'
import json, sys
def flat(p, pre=""):
    out = {}
    for k, v in p.items():
        if "properties" in v: out.update(flat(v["properties"], pre + k + "."))
        else: out[pre + k] = v
    return out
want = flat(json.load(open(sys.argv[1]))["template"]["mappings"]["properties"])
try:
    t = json.loads(sys.argv[2])["index_templates"][0]["index_template"]
    got = flat(t["template"]["mappings"]["properties"])
    sim = flat(json.loads(sys.argv[3])["template"]["mappings"]["properties"])
    overlapping = json.loads(sys.argv[3]).get("overlapping", [])
except Exception as e:
    print("  FAIL  could not parse the cluster response:", e); print(sys.argv[2][:300]); sys.exit(1)
fail = 0
def cmp(name, have):
    global fail
    bad = [f for f, spec in want.items()
           if have.get(f, {}).get("type") != spec["type"]
           or (spec.get("format") and have.get(f, {}).get("format") != spec["format"])]
    print(f"  {'PASS' if not bad else 'FAIL'}  {name}: {len(want) - len(bad)}/{len(want)} declared fields as in the file")
    for f in bad: print(f"          {f}: want {want[f]}, got {have.get(f)}")
    fail += len(bad)
print(f"  index_patterns={t.get('index_patterns')} priority={t.get('priority')}")
cmp("stored template", got)
cmp("simulated new index", sim)
if overlapping:
    print(f"  NOTE  lower-priority templates also match polaris-logs-*: {overlapping} -- the simulate above is the merged result")
sys.exit(1 if fail else 0)
PY
RC=$?
echo
[ "$RC" -eq 0 ] && echo "RESULT: PASS -- tomorrow's polaris-logs-* index is the first one shaped by it." \
                || echo "RESULT: FAIL -- see the field list above."
exit $RC
