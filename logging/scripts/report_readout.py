#!/usr/bin/env python3
"""Read polaris-report summary rows from an OpenSearch _search response on stdin
and say what an empty polaris-logs-* means. Kept as its own file so it can be
tested without shell quoting getting in the way."""
import json, sys

def main(fh, out=sys.stdout):
    try:
        hits = json.load(fh)["hits"]["hits"]
    except Exception as e:
        print(f"  could not read a response: {e}", file=out); return 2
    rows = [h["_source"] for h in hits if h["_source"].get("report_type") == "summary"]
    if not rows:
        seen = sorted({str(h["_source"].get("report_type")) for h in hits})
        print(f"  no summary rows. report_type values present: {seen or 'none'}", file=out)
        print("  If this is empty the report stream is not arriving at all — go back to step 3.", file=out)
        return 1
    hdr = f'  {"window_start":24} {"seen":>6} {"kept":>6} {"counted":>8} {"err":>5} {"skipped":>8}'
    print(hdr, file=out); print("  " + "-" * (len(hdr) - 2), file=out)
    total = 0
    def i(r, k): 
        try: return int(r.get(k, 0) or 0)
        except (TypeError, ValueError): return 0
    for r in rows[:10]:
        total += i(r, "access_seen")
        print(f'  {str(r.get("window_start",""))[:24]:24} {i(r,"access_seen"):>6} '
              f'{i(r,"access_kept"):>6} {i(r,"access_counted"):>8} '
              f'{i(r,"errors_kept"):>5} {i(r,"windows_skipped"):>8}', file=out)
    print(f"\n  {len(rows)} summary row(s); access_seen totals {total}\n", file=out)
    print("  VERDICT:", file=out)
    if total == 0:
        print("  * access_seen is 0 in every window: POLARIS HAD NO TRAFFIC.", file=out)
        print("    An empty polaris-logs-* is the pipeline working, not failing —", file=out)
        print("    policy v3 has nothing to store because nothing was requested.", file=out)
        print("    Drive one API call at Polaris and re-run before concluding anything.", file=out)
    else:
        print(f"  * access_seen totals {total}: the filter SAW access-log records.", file=out)
        print("    An empty polaris-logs-* now means the fault is AFTER the filter:", file=out)
        print("    - kept > 0 but nothing indexed -> the OUTPUT. A 401 from an unexpanded", file=out)
        print("      ${OS_PASSWORD}, or a per-item rejection inside an HTTP 200. Both show", file=out)
        print("      up only in the pod log, via Trace_Error On.", file=out)
        print("    - kept == 0 with counted > 0 -> policy v3 counted every record instead", file=out)
        print("      of storing it. For GET/HEAD 2xx that is CORRECT, not a bug.", file=out)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.stdin))
