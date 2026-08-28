#!/usr/bin/env python3
"""T349 -- pull the per-decision facts out of every scratch hook log."""
import glob
import json
import os
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "/tmp/t349-scratch/out"
print("%-32s %-8s %-20s %-10s %s" % ("run", "tool", "decision", "net_ms", "note"))
for p in sorted(glob.glob(os.path.join(root, "*.hook.jsonl"))):
    tag = os.path.basename(p).replace(".hook.jsonl", "")
    for line in open(p):
        r = json.loads(line)
        note = r.get("err") or r.get("reason") or ""
        print("%-32s %-8s %-20s %-10s %s" % (
            tag, r.get("tool_name"), r.get("decision"),
            r.get("net_ms", ""), str(note)[:70]))
