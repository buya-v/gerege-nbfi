#!/usr/bin/env python3
"""T393 — T382 FINDING 4's ONE-LINE MOVE, applied mechanically so it is exactly one line.

Rewrites `FORK = "<40 hex>"` in the named copy of verify-capture-integrity.py to the given
commit-ish, and prints the OLD value on stdout. Nothing else in the file is touched.

The whole finding is that this is a ONE-LINE change to a constant nothing checked. Doing it
by hand in a transcript would leave "one line" as a claim; doing it with a regex that
REFUSES (exit 2) unless it matches exactly one occurrence makes it a measurement.

argv: <path to verify-capture-integrity.py in a scratch clone> <new 40-hex commit-ish>
"""
import re
import sys

if len(sys.argv) != 3:
    sys.stderr.write("usage: 13-move-fork-constant.py <path> <new-sha>\n")
    sys.exit(2)

PATH, NEW = sys.argv[1], sys.argv[2]
if not re.fullmatch(r"[0-9a-f]{40}", NEW):
    sys.stderr.write("REFUSED: %r is not a 40-hex commit-ish.\n" % NEW)
    sys.exit(2)

with open(PATH, "r", encoding="utf-8") as fh:
    src = fh.read()

pat = re.compile(r'^FORK = "([0-9a-f]{40})"$', re.M)
hits = pat.findall(src)
if len(hits) != 1:
    sys.stderr.write("REFUSED: found %d `FORK = \"<sha>\"` assignments in %s, expected "
                     "exactly 1. The one-line move is only one line if there is one line.\n"
                     % (len(hits), PATH))
    sys.exit(2)

with open(PATH, "w", encoding="utf-8") as fh:
    fh.write(pat.sub('FORK = "%s"' % NEW, src, count=1))
print(hits[0])
sys.exit(0)
