"""Offline check of the rewired cache column against the REAL capture.

Groups statements by mdc.requestId so each group is one request, then profiles
each. Reproduces (or refutes) the documented reference figures.
"""

import sys, pathlib, collections, statistics

sys.path.insert(0, sys.argv[1])
import api_trace as a

log = pathlib.Path(sys.argv[2])
print(f"reading {log.stat().st_size/1e6:.1f} MB ...", flush=True)
stmts = a.parse_polaris_log(log.read_text(errors="replace"))
print(f"parsed {len(stmts)} statements")

by_req = collections.defaultdict(list)
for s in stmts:
    by_req[getattr(s, "request_id", None)].append(s)
by_req.pop(None, None)
print(f"requests with a requestId: {len(by_req)}")

verdicts = collections.Counter()
shares, with_batch = [], 0
for rid, ss in by_req.items():
    p = a.entity_access_profile(ss)
    verdicts[p["verdict"]] += 1
    if p["batched_share"] is not None:
        shares.append(p["batched_share"])
        if p["batch_validate"]:
            with_batch += 1

n = len(by_req)
print("\nverdicts:", dict(verdicts))
print(
    f"requests containing >=1 batched validation: {with_batch}/{n}"
    f" ({100*with_batch/n:.1f}%)"
    if n
    else ""
)
if shares:
    print(f"median batched_share: {statistics.median(shares):.2f}")

shapes = collections.Counter()
for s in stmts:
    sh = a.entity_access_shape(s.sql)
    if sh:
        shapes[sh] += 1
print("\nstatement shapes:")
for k, v in shapes.most_common():
    print(f"  {k:<28} {v}")

old = collections.Counter()
for rid, ss in by_req.items():
    old[a.TraceRecord(api="x", sql=ss).cache_verdict] += 1
print("\nOLD cache_verdict for the same requests:", dict(old))
