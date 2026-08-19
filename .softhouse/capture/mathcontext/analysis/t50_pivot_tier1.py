#!/usr/bin/env python3
"""
T50 -- the Tier 1 grid as 7x7 pivot tables (rows = AMBIENT mode, cols = THREADED mode).

Reads out/t50-tier1.json only.  Contacts no oracle, no server, no database.  Prints every
cell of every (site, value) pair; the ABSENT row is printed too, as `THREW`.

Usage:  python3 analysis/t50_pivot_tier1.py [payload.json]
"""
import collections
import json
import os
import sys

ORDER = ["UP", "DOWN", "CEILING", "FLOOR", "HALF_UP", "HALF_DOWN", "HALF_EVEN"]
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "out", "t50-tier1.json")


def main(path):
    doc = json.load(open(path))
    grid = collections.defaultdict(dict)
    for c in doc["cases"]:
        i = c["inputs"]
        amb = "ABSENT" if i["ambientRoundingModeOrdinal"] is None else i["ambientRoundingModeIntent"]
        grid[(c["site"], c["value"])][(amb, i["threadedRoundingModeIntent"])] = c

    sites, vals = [], []
    for (s, v) in grid:
        if s not in sites:
            sites.append(s)
        if v not in vals:
            vals.append(v)
    sites.sort()
    vals.sort()

    w = 23
    printed = 0
    for site in sites:
        for val in vals:
            cells = grid[(site, val)]
            if not cells:
                continue
            sample = next(iter(cells.values()))
            print("=== %s / %s" % (site, val))
            print("    source     : %s" % sample["siteSource"])
            print("    expression : %s" % sample["siteExpression"])
            print("    inputs     : a=%s percentage=%s  (%s)"
                  % (sample["inputs"]["a"], sample["inputs"]["percentage"], sample["valueWhy"]))
            print("    rows = AMBIENT MoneyHelper mode, cols = THREADED MathContext mode (precision 19)")
            print("    %-10s" % "" + "".join("%-*s" % (w, t) for t in ORDER))
            for a in ["ABSENT"] + ORDER:
                row = []
                for t in ORDER:
                    c = cells.get((a, t))
                    if c is None:
                        row.append("-")
                    elif c["observed"] is None:
                        row.append("THREW")
                    else:
                        row.append(c["observed"])
                    printed += 1
                print("    %-10s" % a + "".join("%-*s" % (w, x) for x in row))
            print()
    print("%d cells printed over %d (site, value) pairs" % (printed, len(grid)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
