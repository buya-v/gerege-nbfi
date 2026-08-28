#!/usr/bin/env python3
"""T145 -- every float() CAST inside a file that has an unguarded json.load.

The sharpest carry signal is not the load, it is the CAST. T207's ruling turns on whether
float() yields only a bool (permitted measurement) or holds an amount (carry). This lists
every float() cast in the unguarded population so each can be read and classified by hand;
the count is stated with its selector so it can be re-measured rather than restated.
"""
import json
import os
import re
import sys

here = os.path.dirname(os.path.abspath(__file__))
c = json.load(open(os.path.join(here, "..", "out", "census.json")))
files = sorted({h["file"] for h in c["hits"] if not h["guarded"]})
print("SELECTOR: regex /\\bfloat\\s*\\(/ over every tracked .py that has >=1 UNGUARDED")
print("          json.load site (out/census.json).")
print("POPULATION: %d files" % len(files))
print()
tot = 0
hits = 0
for f in files:
    lines = open(f, encoding="utf-8", errors="replace").read().split("\n")
    got = False
    for i, l in enumerate(lines, 1):
        if re.search(r"\bfloat\s*\(", l):
            tot += 1
            got = True
            print("%s:%d: %s" % (f, i, l.strip()[:140]))
    if got:
        hits += 1
print()
print("float() CASTS: %d, in %d of the %d unguarded-population files" % (tot, hits, len(files)))
