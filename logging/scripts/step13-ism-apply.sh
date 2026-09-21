#!/usr/bin/env bash
# ============================================================================
# Apply the three ISM retention policies, and prove each one is attached.
#
# WHY THIS EXISTS. Until 2026-09-18 nothing deleted anything: index templates
# fixed the MAPPINGS (step9, step12) but no policy ever removed an index, so
# polaris-logs-*, polaris-report-* and k8s-logs-* grew without bound. Retention
# was recorded as the Monitoring team's (2026-09-16); Kade took the local
# cluster's back on 2026-09-18 and set 3d / 30d / 3d.
#
# TWO THINGS ISM DOES NOT DO, and both have bitten this repo's templates:
#
#   1. ism_template attaches to indices created AFTER the policy is stored.
#      Today's indices are NOT managed by the PUT alone -- they need an
#      explicit _plugins/_ism/add. This script does both and reports each.
#   2. Two policies whose ism_template matches one pattern at the same
#      priority is a COLLISION, and the loser is silent. The preflight below
#      refuses to write anything if an existing policy already claims one of
#      our three patterns. Read the names it prints before overriding.
#
# DESTRUCTIVE, ON A DELAY. This attaches delete actions. An index that is
# already older than its min_index_age is deleted at the next ISM sweep (the
# job runs every 30-60 min by default). polaris-report-* indices written while
# WINDOW_SECONDS was 30 are verification data and WILL go on the first sweep --
# that is handoff task E, and it is the intended outcome, but it is not
# reversible. Read DRY RUN output first.
#
#   export OS_URL=https://192.168.194.1:9200 OS_USER=admin OS_PASSWORD='...'
#   bash logging/scripts/step13-ism-apply.sh            # preflight + dry run, writes nothing
#   bash logging/scripts/step13-ism-apply.sh --apply    # PUT policies, add to existing
# ============================================================================
set -uo pipefail
: "${OS_URL:?}"; : "${OS_USER:?}"; : "${OS_PASSWORD:?}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1
OS=(curl -sS -k --max-time 30 -u "${OS_USER}:${OS_PASSWORD}" -H 'Content-Type: application/json')

# policy_id : file : pattern
POLICIES=(
  "polaris-logs-3d:${HERE}/opensearch/ism-polaris-logs-3d.json:polaris-logs-*"
  "polaris-report-30d:${HERE}/opensearch/ism-polaris-report-30d.json:polaris-report-*"
  "k8s-logs-3d:${HERE}/opensearch/ism-k8s-logs-3d.json:k8s-logs-*"
)

# ---------------------------------------------------------------------------
# SELF-CHECK: compile every embedded Python block before running any of them.
#
# WHY. On 2026-09-18 this script shipped with sections 3 and 4 written as
# `python3 -c '...'` containing \" escapes. Single-quoted shell passes the
# backslashes through verbatim, and a backslash inside an f-string expression is
# a SyntaxError -- so both sections crashed at the point where they were meant to
# report what OpenSearch said, after their curl had already run. The apply failed
# and took its own error message with it.
#
# It escaped testing because the offline smoke test could not reach a cluster, so
# the preflight (correctly) aborted at section 1 and sections 3-5 were never
# executed. A gate that stops early hides everything behind it: this compiles all
# of it, with no cluster, every run.
# ---------------------------------------------------------------------------
python3 - "${BASH_SOURCE[0]}" <<'PY' || { echo "REFUSING TO RUN: embedded Python does not compile."; exit 1; }
import sys, re
src = open(sys.argv[1], encoding="utf-8").read().splitlines()
blocks, cur = [], None
for i, line in enumerate(src, 1):
    if cur is None:
        if re.search(r"<<'PY'", line):
            cur = (i + 1, [])
    elif line.strip() == "PY" and not line.startswith(" "):
        blocks.append((cur[0], "\n".join(cur[1]))); cur = None
    else:
        cur[1].append(line)
bad = 0
for start, code in blocks:
    if "SELF-CHECK" in code or "import sys, re" in code:
        continue
    try:
        compile(code, f"<block at line {start}>", "exec")
    except SyntaxError as e:
        bad += 1
        print(f"  FAIL  block at line {start}: {e.msg} (block line {e.lineno})")
print(f"  self-check: {len(blocks) - bad}/{len(blocks)} embedded Python blocks compile")
sys.exit(1 if bad else 0)
PY
echo

echo "== 0. the files parse, and say what they are expected to say =="
python3 - "${POLICIES[@]}" <<'PY' || exit 1
import json, sys
want = {"polaris-logs-3d": "3d", "polaris-report-30d": "30d", "k8s-logs-3d": "3d"}
bad = 0
for spec in sys.argv[1:]:
    pid, path, pattern = spec.split(":", 2)
    try:
        p = json.load(open(path))["policy"]
    except Exception as e:
        print(f"  FAIL  {path}: {e}"); bad += 1; continue
    age = p["states"][0]["transitions"][0]["conditions"]["min_index_age"]
    pats = p["ism_template"][0]["index_patterns"]
    names = [s["name"] for s in p["states"]]
    ok = (p["policy_id"] == pid and age == want[pid] and pats == [pattern]
          and "delete" in names
          and any("delete" in a for a in p["states"][-1]["actions"]))
    print(f"  {'PASS' if ok else 'FAIL'}  {pid:<20} age={age:<4} patterns={pats} states={names}")
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
PY
echo

echo "== 1. PREFLIGHT: does any EXISTING policy already claim our patterns? =="
# An unreachable cluster must not read as "no collisions" -- that is #43's shape, a check
# that passes by failing to run. This section exits non-zero on BOTH a clash and an
# unreadable response, and PRE below blocks --apply either way.
EXISTING=$("${OS[@]}" "${OS_URL}/_plugins/_ism/policies?size=200")
PRE=0
python3 - "$EXISTING" "${POLICIES[@]}" <<'PY'
import json, sys, fnmatch
raw, specs = sys.argv[1], sys.argv[2:]
mine = {s.split(":", 2)[0]: s.split(":", 2)[2] for s in specs}
try:
    pols = json.loads(raw).get("policies", [])
except Exception as e:
    print("  FAIL  could not read the policy list -- the cluster did not answer.")
    print(f"        {e}: {raw[:200]!r}")
    print("        This is NOT 'no collisions'. Fix OS_URL/credentials and re-run.")
    sys.exit(2)
if not pols:
    print("  no ISM policies exist on this cluster -- nothing can collide.")
clash = 0
for p in pols:
    pid = p.get("_id") or p.get("policy_id")
    for t in (p.get("policy", {}).get("ism_template") or []):
        for pat in t.get("index_patterns", []):
            for my_id, my_pat in mine.items():
                if pid == my_id:
                    print(f"  ours   {pid:<20} claims {pat} (priority {t.get('priority')}) -- will be REPLACED")
                elif fnmatch.fnmatch(my_pat.replace('*', 'X'), pat) or fnmatch.fnmatch(pat.replace('*', 'X'), my_pat):
                    print(f"  CLASH  {pid:<20} claims {pat} (priority {t.get('priority')}) vs our {my_pat}")
                    clash += 1
print(f"  -> {clash} collision(s).", "Resolve before --apply." if clash else "Clear.")
sys.exit(1 if clash else 0)
PY
PRE=$?
echo

echo "== 2. indices that exist today, and whether ISM manages them =="
for spec in "${POLICIES[@]}"; do
  PID="${spec%%:*}"; PATTERN="${spec##*:}"
  EXPL=$("${OS[@]}" "${OS_URL}/_plugins/_ism/explain/${PATTERN}")
  echo "  ${PATTERN}"
  python3 - "$EXPL" <<'PY'
import json, sys
try:
    d = json.loads(sys.argv[1])
except Exception as e:
    print(f"    (explain unreadable: {e})"); sys.exit(0)
rows = [(k, v) for k, v in d.items() if isinstance(v, dict)]
if not rows:
    print("    no indices match this pattern yet")
for idx, body in sorted(rows):
    pid = body.get("index.plugins.index_state_management.policy_id") or body.get("policy_id") or "UNMANAGED"
    print(f"    {idx:<34} policy={pid}")
PY
done
echo

if [ "$PRE" -ne 0 ]; then
  echo "PREFLIGHT NOT CLEAR (section 1 exited ${PRE}: 1=collision, 2=cluster unreadable)."
  echo "Nothing was written. --apply is refused until this is green."
  exit 1
fi

if [ "$APPLY" -eq 0 ]; then
  echo "DRY RUN -- nothing was written. Preflight is clear; re-run with --apply."
  exit 0
fi

echo "== 3. PUT the policies =="
FAIL=0
for spec in "${POLICIES[@]}"; do
  PID="${spec%%:*}"; REST="${spec#*:}"; FILE="${REST%%:*}"
  # An existing policy needs its seq_no/primary_term, or OpenSearch answers 409.
  CUR=$("${OS[@]}" "${OS_URL}/_plugins/_ism/policies/${PID}")
  Q=$(python3 - "$CUR" <<'PY'
import json, sys
try:
    d = json.loads(sys.argv[1])
    print("?if_seq_no=%s&if_primary_term=%s" % (d["_seq_no"], d["_primary_term"]))
except Exception:
    print("")
PY
)
  RESP=$("${OS[@]}" -X PUT "${OS_URL}/_plugins/_ism/policies/${PID}${Q}" --data-binary "@${FILE}")
  python3 - "$RESP" "$PID" <<'PY' || FAIL=1
import json, sys
raw, pid = sys.argv[1], sys.argv[2]
try:
    r = json.loads(raw)
except Exception as e:
    print("  FAIL  %s: response was not JSON (%s)" % (pid, e))
    print("        raw: %r" % raw[:500]); sys.exit(1)
if "_id" in r:
    print("  PASS  stored %s (version %s)" % (r["_id"], r.get("_version")))
    sys.exit(0)
# Print the WHOLE error. The first version of this script truncated to 300 chars and
# then crashed before printing anything at all -- the reason an apply failed on
# 2026-09-18 was destroyed by its own reporting.
print("  FAIL  %s rejected. OpenSearch said:" % pid)
print(json.dumps(r, indent=2)[:4000])
sys.exit(1)
PY
done
echo

# Do not attach a policy that may not exist. Section 4 on a failed section 3 produces
# noise that looks like a second, different problem.
if [ "$FAIL" -ne 0 ]; then
  echo "ABORTING before section 4: at least one policy was not stored."
  echo "Nothing was attached. Fix the rejection above and re-run --apply; the PUT is idempotent."
  exit 1
fi

echo "== 3b. READ BACK: the policies are on the cluster, independent of what the PUT replied =="
LIST=$("${OS[@]}" "${OS_URL}/_plugins/_ism/policies?size=200")
python3 - "$LIST" "${POLICIES[@]}" <<'PY' || FAIL=1
import json, sys
raw, specs = sys.argv[1], sys.argv[2:]
want = {sp.split(":", 2)[0] for sp in specs}
try:
    pols = json.loads(raw).get("policies", [])
except Exception as e:
    print("  FAIL  could not read the policy list back (%s)" % e); sys.exit(1)
have = {}
for p in pols:
    pid = p.get("_id") or p.get("policy_id")
    body = p.get("policy", {})
    try:
        age = body["states"][0]["transitions"][0]["conditions"]["min_index_age"]
    except Exception:
        age = "?"
    have[pid] = age
bad = 0
for pid in sorted(want):
    ok = pid in have
    print("  %s  %-20s %s" % ("PASS" if ok else "FAIL", pid,
          ("stored, min_index_age=" + have[pid]) if ok else "NOT ON THE CLUSTER"))
    bad += 0 if ok else 1
sys.exit(1 if bad else 0)
PY
if [ "$FAIL" -ne 0 ]; then
  echo "ABORTING: a policy the PUT claimed to store is not in the policy list."
  exit 1
fi
echo

echo "== 4. attach to indices that already exist (ism_template only covers new ones) =="
for spec in "${POLICIES[@]}"; do
  PID="${spec%%:*}"; PATTERN="${spec##*:}"
  RESP=$("${OS[@]}" -X POST "${OS_URL}/_plugins/_ism/add/${PATTERN}" \
         -d "{\"policy_id\":\"${PID}\"}")
  echo "  ${PATTERN} -> ${PID}"
  python3 - "$RESP" <<'PY'
import json, sys
raw = sys.argv[1]
try:
    r = json.loads(raw)
except Exception as e:
    print("    could not parse the add response (%s): %r" % (e, raw[:400])); sys.exit(0)
for f in (r.get("failed_indices") or []):
    print("    note %s: %s" % (f.get("index_name"), f.get("reason")))
print("    updated=%s failures=%s" % (r.get("updated_indices", 0), r.get("failures")))
PY
done
echo

echo "== 5. VERIFY: every matching index names the policy we just stored =="
python3 - "$OS_URL" "$OS_USER" "$OS_PASSWORD" "${POLICIES[@]}" <<'PY'
import json, subprocess, sys
url, user, pw, specs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
bad = total = 0
for spec in specs:
    pid, _, pattern = spec.split(":", 2)
    out = subprocess.run(["curl", "-sS", "-k", "--max-time", "30", "-u", f"{user}:{pw}",
                          f"{url}/_plugins/_ism/explain/{pattern}"],
                         capture_output=True, text=True).stdout
    try:
        d = json.loads(out)
    except Exception as e:
        print(f"  FAIL  {pattern}: explain unreadable ({e})"); bad += 1; continue
    rows = [(k, v) for k, v in d.items() if isinstance(v, dict)]
    if not rows:
        # Not a pass and not a failure: there is nothing to manage yet.
        print(f"  ----  {pattern}: no indices exist; ism_template covers the next one")
        continue
    for idx, body in sorted(rows):
        total += 1
        got = body.get("index.plugins.index_state_management.policy_id") or body.get("policy_id")
        ok = got == pid
        bad += 0 if ok else 1
        print(f"  {'PASS' if ok else 'FAIL'}  {idx:<34} policy={got} (want {pid})")
print(f"\n  {total - bad}/{total} existing indices managed as declared.")
sys.exit(1 if bad else 0)
PY
RC=$?

echo
echo "REMINDER: ism_template binds at index creation. Tomorrow's polaris-logs-YYYY.MM.DD"
echo "picks its policy up automatically; today's needed section 4. Deletion happens on the"
echo "ISM sweep (every 30-60 min), not at this script's exit -- re-run the dry run later to"
echo "watch state move hot -> delete."
[ "$FAIL" -eq 0 ] && [ "$RC" -eq 0 ] \
  && echo "RESULT: PASS -- three policies stored and every existing index is managed." \
  || echo "RESULT: FAIL -- see above."
[ "$FAIL" -eq 0 ] && exit $RC || exit 1
