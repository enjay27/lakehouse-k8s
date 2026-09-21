#!/usr/bin/env python3
"""Turn the step10 readouts' tier1.json into inputs for the refactor harnesses.

    python3 logging/candidates/tier1-to-lua.py            # reads .scratch/readout-*/tier1.json
    -> /tmp/tier1_all.lua  (diff-refactor.lua, bench-refactor.lua)
    -> /tmp/paths.txt      (bench-classify.lua)

Records are FILTER 3 input as the pipeline sees it: `message` renamed to `_msg`, `@timestamp` kept as `_time`,
the record time in epoch seconds as `now` (the harnesses feed it as _now_override).
"""
import datetime, glob, json, re

def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "") + '"'

out, paths = ["return {"], []
for f in sorted(glob.glob(".scratch/readout-*/tier1.json")):
    for r in json.load(open(f)):
        ts = r.get("@timestamp", "")
        t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() if ts else 0
        rid = (r.get("mdc") or {}).get("requestId")
        out.append("{loggerName=%s,level=%s,_msg=%s,_time=%s,now=%d%s}," % (
            q(r.get("loggerName", "")), q(r.get("level", "")), q(r.get("message", "")), q(ts), int(t),
            (",mdc={requestId=%s}" % q(rid)) if rid else ""))
        if r.get("loggerName") == "io.quarkus.http.access-log":
            m = re.match(r'^\S+ \S+ \S+ \[[^\]]*\] "[A-Z]+ (\S+)', r.get("message", ""))
            if m:
                paths.append(m.group(1))
out.append("}")
open("/tmp/tier1_all.lua", "w").write("\n".join(out))
open("/tmp/paths.txt", "w").write("\n".join(paths) + "\n")
print(f"{len(out) - 2} records -> /tmp/tier1_all.lua, {len(paths)} access paths -> /tmp/paths.txt")
