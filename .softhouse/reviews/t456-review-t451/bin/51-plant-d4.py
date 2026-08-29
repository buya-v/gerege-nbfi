#!/usr/bin/env python3
"""T456 -- P-22 on T451's OWN instrument: a FOURTH planted defect, of the reviewer's
design, chosen to be one the author's three could not have found.

T451 planted three defects into `reconcile_action` (D1 wrong polarity, D2 arm deleted,
D3 T312 suffix no longer stripped) and its 288-state enumeration caught all three.  All
three break the lattice's WELL-FORMEDNESS -- they make a state have no verdict, two
verdicts, or a verdict that disagrees with the instrument's transcription of the arms.

D4 IS A ROUTING DEFECT IN `_branch_wip_core`, NOT AN ARM DEFECT.  It swaps the order of
the two new tests:

    if carriers:                    ->    if carriers is None or unprobed:
        return "stillborn-carried"            return "indeterminate"
    if carriers is None or unprobed:      if carriers:
        return "indeterminate"                return "stillborn-carried"

The lattice stays perfectly single-valued.  Every kind still maps to exactly one
polarity.  `arms_matching` still agrees with `reconcile_action`, because
`reconcile_action` is untouched.  What changes is that a state where a live ref CARRIES
CONTENT *and* another ref went unprobed now DEMOTES instead of REFUSING -- i.e. the exact
C-T449-1 fail-open the branch was written to close, reintroduced for the subset of
states where the ref probe was partially budget-starved.  That subset is not exotic: it
is precisely what `REF_PROBE_SECONDS` truncation produces on a loaded host.

The question this instrument answers is therefore: IS THE 288-STATE ENUMERATION A
CORRECTNESS CHECK, OR ONLY A WELL-FORMEDNESS CHECK?

usage: 51-plant-d4.py <green.py> <partition.py> <direction.py> <workdir>
"""
import os
import shutil
import subprocess
import sys

GREEN, PART, DIRN, WORK = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(WORK, exist_ok=True)

BEFORE = '''        if carriers:
            return "stillborn-carried", ('''
if not os.path.exists(GREEN):
    sys.exit("ABORT: %s missing" % GREEN)
src = open(GREEN, encoding="utf-8").read()

# Locate the two blocks by their unique anchors and swap them.  Verified UNIQUE before
# writing: an instrument that plants nothing and then reports "caught 0" is the failure
# mode this whole exercise exists to avoid.
A0 = src.index('        if carriers:\n            return "stillborn-carried"')
A1 = src.index('        if carriers is None or unprobed:', A0)
A2 = src.index('        return "stillborn", (', A1)
blockA = src[A0:A1]          # the stillborn-carried arm
blockB = src[A1:A2]          # the indeterminate arm
if src.count('        if carriers:\n            return "stillborn-carried"') != 1:
    sys.exit("ABORT: the stillborn-carried arm is not unique; refusing to plant")
if not blockA.strip() or not blockB.strip():
    sys.exit("ABORT: one of the two blocks came out empty; refusing to plant")
planted = src[:A0] + blockB + blockA + src[A2:]
if planted == src:
    sys.exit("ABORT: the plant was a no-op. NOTHING WAS TESTED.")

dst = os.path.join(WORK, "rt_d4.py")
open(dst, "w", encoding="utf-8").write(planted)
bs = os.path.join(os.path.dirname(GREEN), "branch_sweep.py")
if os.path.exists(bs):
    shutil.copy(bs, os.path.join(WORK, "branch_sweep.py"))

print("D4 PLANTED into %s" % dst)
print("   swapped a %d-char arm with a %d-char arm; files differ by %d bytes"
      % (len(blockA), len(blockB), abs(len(planted) - len(src))))
print("   PROOF THE PLANT IS LIVE (the two arms now appear in the opposite order):")
for probe in ('if carriers is None or unprobed:', 'if carriers:'):
    print("      first occurrence of %-36r at offset %d"
          % (probe, planted.index("        " + probe)))
print()

print("=" * 78)
print("LEG 1 -- T451's 288-state partition, GREEN vs D4-PLANTED GREEN")
print("=" * 78)
r = subprocess.run([sys.executable, PART, GREEN, dst], capture_output=True, text=True)
print(r.stdout + r.stderr)

print("=" * 78)
print("LEG 2 -- T456's per-state direction check, GREEN (clean) vs D4-PLANTED GREEN")
print("=" * 78)
r2 = subprocess.run([sys.executable, DIRN, GREEN, dst], capture_output=True, text=True)
print(r2.stdout + r2.stderr)
print("LEG 2 exit code: %d  (non-zero == the defect was CAUGHT)" % r2.returncode)
