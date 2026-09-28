#!/usr/bin/env python3
"""Turn a copy of the OpenSearch Dashboards Dev Tools response panel into valid JSON.

    python3 logging/scripts/devtools-json-fix.py panel-copy.json > fixed.json

The console shows strings that contain newlines as \"\"\"...\"\"\" and re-indents their continuation
lines. This restores valid JSON (each triple-quoted block becomes a JSON string). It CANNOT restore the
original indentation inside those strings -- for byte-exact exports use "Copy as cURL" or curl.
Prints how many values were converted to stderr. See logging/opensearch/devtools-export.console.
"""

import json
import re
import sys

if len(sys.argv) != 2:
    sys.exit(__doc__)
raw = open(sys.argv[1], encoding="utf-8").read()
n = 0


def conv(m):
    global n
    n += 1
    return json.dumps(m.group(1), ensure_ascii=False)


fixed = re.sub(r'"""(.*?)"""', conv, raw, flags=re.S)
doc = json.loads(fixed)
json.dump(doc, sys.stdout, ensure_ascii=False, indent=1)
sys.stdout.write("\n")
print(
    f"converted {n} triple-quoted value(s); whitespace inside multi-line strings may differ from the index",
    file=sys.stderr,
)
