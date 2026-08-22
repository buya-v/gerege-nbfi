#!/usr/bin/env python3
"""T203 - enumerate, per promote script, which LIVE vectors it would write over.

Reads the four scripts' source, extracts every `*.json` string literal, and
intersects with the files that actually exist under
`.softhouse/vectors/loanschedule/` in this worktree.  READ-ONLY: this script
opens nothing for writing and executes none of the promote scripts.
"""
import os
import re
import sys

STORE = ".softhouse/vectors/loanschedule"
TARGETS = [
    ("T74", ".softhouse/handoff/T74-promote-vectors.py", "truncating"),
    ("T61", ".softhouse/handoff/T61-promote-vectors.py", "truncating"),
    ("T64", ".softhouse/capture/t64-zeroprincipal/src/T64-promote-vectors.py",
     "truncating"),
    ("T58", ".softhouse/handoff/T58-promote-vectors.py", "refuses-overwrite"),
]

union = set()
for name, path, kind in TARGETS:
    src = open(path, "r", encoding="utf-8").read()
    names = sorted(set(re.findall(r'"([A-Za-z0-9_.\-]+\.json)"', src)))
    live = [n for n in names if os.path.isfile(os.path.join(STORE, n))]
    dead = [n for n in names if n not in live]
    print("%s (%s)  %s" % (name, kind, path))
    print("  json-name literals: %d ; LIVE in store: %d" % (len(names), len(live)))
    for n in live:
        print("    LIVE          %s" % n)
    for n in dead:
        print("    not-in-store  %s" % n)
    if kind == "truncating":
        union |= set(live)
    print()

print("UNION of LIVE vectors reachable by the THREE truncating scripts: %d"
      % len(union))
for n in sorted(union):
    print("   %s" % n)

total = len([f for f in os.listdir(STORE) if f.endswith(".json")])
print("\nfiles in %s: %d" % (STORE, total))
if total == 0:
    sys.stderr.write("P-35: inspected ZERO store files - ERROR\n")
    sys.exit(1)
