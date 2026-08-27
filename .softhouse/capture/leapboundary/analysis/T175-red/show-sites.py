#!/usr/bin/env python3
"""T175 -- print the source context of every site the swallow census found, so the
load-bearing/incidental classification below it is a HAND-READ of the code and not a guess
from a one-line body. Read-only. Usage: python3 show-sites.py <census-output.txt> [root]"""
import os
import re
import sys


def main(argv):
    census, root = argv[0], (argv[1] if len(argv) > 1 else os.getcwd())
    rows = []
    for line in open(census):
        m = re.match(r"^\d+\s+(\S+\.py)\s+(\d+)\s+(except.*)", line)
        if m:
            rows.append((m.group(1), int(m.group(2)), m.group(3).strip()))
    for f, ln, clause in rows:
        p = os.path.join(root, f)
        src = open(p).read().splitlines()
        lo, hi = max(0, ln - 9), min(len(src), ln + 3)
        print("=" * 100)
        print("%s:%d   %s" % (f, ln, clause))
        print("=" * 100)
        for i in range(lo, hi):
            print("%6d %s%s" % (i + 1, ">> " if i + 1 == ln else "   ", src[i]))
        print()
    print("sites shown: %d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
