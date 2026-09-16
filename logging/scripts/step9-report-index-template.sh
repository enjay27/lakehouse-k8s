#!/usr/bin/env bash
# ============================================================================
# Apply the polaris-report-* index template, and prove it took.
#
# WHY THIS EXISTS. Run 1789026666 (2026-09-10) found `min_record_time` mapped as
# TEXT in polaris-report-2026.09.10. Nothing wrote it wrong: the Lua wrote "" on
# an idle window, OpenSearch dynamic-mapped the field from that first document,
# and dynamic mapping is FOR THE LIFE OF THE INDEX. At 30s windows the first
# window of a day is almost always idle, so this recurs every midnight until a
# template exists. The invariant is still checkable client-side (RFC3339 sorts
# and parses), but no range query and no date histogram works on that index.
#
# ORDER MATTERS. The Lua must OMIT the key when nil first -- it does, since
# 2026-09-10 -- because with `date` mapping a document carrying "" is REJECTED
# PER ITEM inside a _bulk that still returns HTTP 200. Losing summary rows that
# way is worse than the text mapping: since policy v3 a successful read exists
# ONLY as an aggregate in this stream. `ignore_malformed: true` on both fields
# is the belt to that braces -- a surprise value costs the field, not the doc.
# Deliberate, because a silently dropped report is the failure this pipeline
# keeps rediscovering.
#
# NOT RETROACTIVE. Indices already created keep their mappings. This takes
# effect on the next daily index (or on one you reindex yourself).
#
#   export OS_URL=https://192.168.194.1:9200 OS_USER=admin OS_PASSWORD='...'
#   bash logging/scripts/step9-report-index-template.sh
# ============================================================================
set -uo pipefail
: "${OS_URL:?}"; : "${OS_USER:?}"; : "${OS_PASSWORD:?}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL="${HERE}/opensearch/polaris-report-template.json"
OS=(curl -sS -k --max-time 30 -u "${OS_USER}:${OS_PASSWORD}" -H 'Content-Type: application/json')

echo "== PUT _index_template/polaris-report =="
"${OS[@]}" -X PUT "${OS_URL}/_index_template/polaris-report" --data-binary "@${TPL}"; echo

echo
echo "== read back + simulate, EVERY field compared with the file (not a grep | head) =="
# 2026-09-16: the first version piped the read-back through `head -20`, which showed 19 of
# the 35 `long` fields and proved nothing about the rest -- the v4 fields sit at the end.
TPL_JSON=$("${OS[@]}" "${OS_URL}/_index_template/polaris-report")
SIM_JSON=$("${OS[@]}" -X POST "${OS_URL}/_index_template/_simulate_index/polaris-report-9999.12.31")
python3 - "$TPL" "$TPL_JSON" "$SIM_JSON" <<'PY'
import json, sys
want = json.load(open(sys.argv[1]))["template"]["mappings"]["properties"]
def props_of_template(raw):
    t = json.loads(raw)["index_templates"][0]["index_template"]
    return t["template"]["mappings"]["properties"], t.get("priority"), t.get("index_patterns")
def props_of_sim(raw):
    return json.loads(raw)["template"]["mappings"]["properties"]
try:
    got, prio, pats = props_of_template(sys.argv[2]); sim = props_of_sim(sys.argv[3])
except Exception as e:
    print("  FAIL  could not parse the cluster response:", e); print(sys.argv[2][:300]); sys.exit(1)
fail = 0
def cmp(name, have):
    global fail
    bad = [f for f, spec in want.items() if have.get(f, {}).get("type") != spec["type"]
           or any(k in spec and have.get(f, {}).get(k) != spec[k] for k in ("index",))]
    print(f"  {'PASS' if not bad else 'FAIL'}  {name}: {len(want) - len(bad)}/{len(want)} fields typed as in the file")
    for f in bad: print(f"          {f}: want {want[f]['type']}, got {have.get(f, {}).get('type')}")
    fail += len(bad)
print(f"  index_patterns={pats} priority={prio}")
cmp("stored template", got)
cmp("simulated new index", sim)
# v6 (2026-09-16): undeclared strings are shaped by dynamic_templates -- compare them too.
want_dt = json.load(open(sys.argv[1]))["template"]["mappings"].get("dynamic_templates", [])
got_dt = json.loads(sys.argv[2])["index_templates"][0]["index_template"]["template"]["mappings"].get("dynamic_templates", [])
sim_dt = json.loads(sys.argv[3])["template"]["mappings"].get("dynamic_templates", [])
for name, have in (("stored dynamic_templates", got_dt), ("simulated dynamic_templates", sim_dt)):
    same = json.dumps(have, sort_keys=True) == json.dumps(want_dt, sort_keys=True)
    print(f"  {'PASS' if same else 'FAIL'}  {name}: {'as in the file' if same else '!= file: ' + json.dumps(have)[:300]}")
    fail += 0 if same else 1
for f in ("app_dropped_total", "dropped", "commit_count", "commit_ms_sum", "commit_ms_min", "commit_ms_max"):
    print(f"        v4 {f:<18} template={got.get(f, {}).get('type')}  simulated={sim.get(f, {}).get('type')}")
sys.exit(1 if fail else 0)
PY
RC=$?

echo
echo "== existing indices keep their mapping for life (informational) =="
"${OS[@]}" "${OS_URL}/polaris-report-*/_mapping/field/min_record_time" | python3 -c '
import json,sys
for idx, body in sorted(json.load(sys.stdin).items()):
    m = body.get("mappings", {}).get("min_record_time", {}).get("mapping", {})
    t = next(iter(m.values()), {}).get("type", "absent")
    print(f"  {idx:<28} min_record_time: {t}")'

echo
echo "text on 09.09 / 09.10 / 09.14 is permanent (#25). date on indices created after the Lua stopped"
echo "writing \"\" (2026-09-10) came from dynamic mapping -- correct, but only the template guarantees it."
[ "$RC" -eq 0 ] && echo "RESULT: PASS -- template stored and every field simulates as declared." \
                || echo "RESULT: FAIL -- see the field list above."
exit $RC
