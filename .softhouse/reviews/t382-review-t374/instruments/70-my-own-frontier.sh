#!/bin/bash
# T382 — my OWN instruments must not move the dead-path frontier. This names every row my
# review adds, before I commit, so the bar is not the first thing to find out.
set -u
O=/tmp/t382-out
mkdir -p "$O"
python3 .softhouse/capture/t316-dead-path-guards/census_dead_paths.py --json "$O/census-mine.json" > "$O/census-mine.txt" 2>&1
echo "census rc=$?"
tail -1 "$O/census-mine.txt"
echo
echo "--- rows my review contributes ---"
python3 - "$O/census-mine.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
rows = d.get("rows") or d.get("dead") or []
mine = [r for r in rows if "t382-review-t374" in (r[0] if isinstance(r, list) else r.get("file", ""))]
for r in rows:
    f = r[0] if isinstance(r, list) else r.get("file")
    l = r[1] if isinstance(r, list) else r.get("literal")
    if "t382-review-t374" in f:
        print("  %s | %s" % (f, l))
print("count:", sum(1 for r in rows
                    if "t382-review-t374" in (r[0] if isinstance(r, list) else r.get("file"))))
print("total rows:", len(rows))
PY
