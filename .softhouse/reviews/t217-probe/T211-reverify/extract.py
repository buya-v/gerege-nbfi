#!/usr/bin/env python3
"""T211 -- extract the REAL bytes under test out of a given fire-program.sh.

The probe must measure the shipped code, not a paraphrase of it (P-55: a probe
that re-implements its subject confirms the re-implementation).  So both the
trap block and run_driver are lifted verbatim, by anchor, from whichever
fire-program.sh is named on the command line -- pre-fix (git show of main) or
post-fix (the worktree copy).

usage: extract.py <fire-program.sh> <outdir>
writes  <outdir>/traps.zsh   and  <outdir>/driver.zsh
and prints the line ranges it took, so the extraction itself is auditable.
"""
import sys

src, outdir = sys.argv[1:3]
lines = open(src, encoding="utf-8").read().splitlines(keepends=True)


def find(pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    raise SystemExit("anchor not found in %s" % src)


# ---- trap block: from `LOCK_RELEASED=0` through the line `trap release_lock EXIT`
t0 = find(lambda l: l.startswith("LOCK_RELEASED=0"))
t1 = find(lambda l: l.rstrip() == "trap release_lock EXIT", t0)
traps = "".join(lines[t0:t1 + 1])

# ---- run_driver: from `run_driver() {` to the first line that is exactly `}`
d0 = find(lambda l: l.startswith("run_driver() {"))
d1 = find(lambda l: l.rstrip() == "}", d0)
driver = "".join(lines[d0:d1 + 1])

open(outdir + "/traps.zsh", "w", encoding="utf-8").write(traps)
open(outdir + "/driver.zsh", "w", encoding="utf-8").write(driver)
print("extracted from %s" % src)
print("  trap block : lines %d-%d  (%d lines, %d bytes)"
      % (t0 + 1, t1 + 1, t1 - t0 + 1, len(traps)))
print("  run_driver : lines %d-%d  (%d lines, %d bytes)"
      % (d0 + 1, d1 + 1, d1 - d0 + 1, len(driver)))
print("  run_driver first line : %s" % lines[d0].rstrip())
print("  run_driver last  line : %s" % lines[d1].rstrip())
