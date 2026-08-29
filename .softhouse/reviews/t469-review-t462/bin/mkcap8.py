#!/usr/bin/env python3
"""Rebuild the PRE-T451 COUNT CAP out of main's own bytes, and PROVE the transform is
live before anything is reported through it.

Pre-T451 (`0bf11587^`) truncated with `for ref in refs[:MAX_REFS_PROBED]` at
MAX_REFS_PROBED = 8, and had NO clock arm at all.  The truncation SET it produced is
therefore exactly {refs at index >= 8}.  Reproducing that set inside T451's loop needs
two edits and no more:
    MAX_REFS_PROBED = 512   ->   8
    elif <clock arm>        ->   elif False:
Each needle is asserted UNIQUE before it is written.
"""
import re
import sys

src = open(sys.argv[1]).read()
dst = sys.argv[2]

n1 = "MAX_REFS_PROBED = 512"
n2 = "    elif time.monotonic() - started > REF_PROBE_SECONDS:"
for n in (n1, n2):
    c = src.count(n)
    if c != 1:
        sys.exit("REFUSING TO PLANT: needle %r matched %d sites, not 1" % (n, c))

out = src.replace(n1, "MAX_REFS_PROBED = 8")
out = out.replace(n2, "    elif False:  # T469 CAP8: clock arm disabled")
open(dst, "w").write(out)

# liveness, checked on the WRITTEN file rather than asserted about the intent
w = open(dst).read()
assert "MAX_REFS_PROBED = 8" in w, "cap not written"
assert "elif False:  # T469 CAP8" in w, "clock arm not disabled"
assert "elif time.monotonic() - started > REF_PROBE_SECONDS:" not in w, "clock arm survived"
assert w != src, "transform was a no-op"
print("CAP8 built from %s -> %s ; both needles unique; transform verified LIVE"
      % (sys.argv[1], dst))
