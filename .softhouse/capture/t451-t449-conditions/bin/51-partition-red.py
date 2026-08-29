#!/usr/bin/env python3
"""T451 -- P-22 for 50-partition.py: DRIVE THE ENUMERATION RED.

A guard that has only ever been seen to pass is not a guard.  50-partition.py reports
0 / 0 / 0 on both RED and GREEN, and that number is worth nothing until the instrument
has been watched to FAIL on defects it is supposed to catch.  Three are planted into
copies of the shipped file, one at a time, each the realistic mistake for this change:

  D1  the new `stillborn-carried` arm returns "demote" instead of "REFUSE"
      -- i.e. the fix is wired but backwards.
  D2  the new arm is DELETED, so `stillborn-carried` falls past the `startswith` tests
      into the fall-through demote -- the exact trap the code comment at
      reconcile_action warns about: a guard that compiles, reads fine and does nothing.
  D3  reconcile_action stops stripping T312's `/CASE-VARIANT` suffix, so one state has
      two verdicts depending on whether the suffix is present.

Each planted file is verified to differ from the original before it is run: a defect
that failed to plant would produce a green run that proves nothing.
"""
import os, subprocess, sys

GREEN = sys.argv[1] if len(sys.argv) > 1 else ".softhouse/bin/ready-tasks.py"
RED = sys.argv[2] if len(sys.argv) > 2 else "/tmp/t451/mods/rt_red.py"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = "/tmp/t451/mods"
os.makedirs(WORK, exist_ok=True)
src = open(GREEN, encoding="utf-8").read()

ARM = '''    if base == "stillborn-carried":'''
RET = '''        return ("REFUSE to demote -- the branch never moved off the dispatch commit, "
                "BUT a live ref CARRIES CONTENT for this task's id under another name; "
                "`needs_retry` would offer for re-dispatch a line that still exists")'''
STRIP = '''    base = (kind or "").split("/")[0]'''

DEFECTS = [
    ("D1 arm returns the WRONG POLARITY",
     RET, '        return "demote to needs_retry"'),
    ("D2 arm DELETED -- falls through to the bottom demote",
     ARM, '    if base == "stillborn-carried-NEVER-MATCHES":'),
    ("D3 T312 suffix no longer stripped",
     STRIP, '    base = (kind or "")'),
]

fail = 0
for label, needle, repl in DEFECTS:
    if src.count(needle) != 1:
        sys.exit("CANNOT PLANT %s (%d sites) -- refusing to report a drive that did not "
                 "run" % (label, src.count(needle)))
    planted = src.replace(needle, repl)
    assert planted != src
    path = os.path.join(WORK, "rt_red_%s.py" % label.split()[0])
    open(path, "w", encoding="utf-8").write(planted)
    out = subprocess.run([sys.executable, os.path.join(HERE, "50-partition.py"),
                          RED, path], capture_output=True, text=True).stdout
    tail = out.split("GREEN (this tree)")[-1]
    lines = [l for l in tail.splitlines()
             if "NO usable verdict" in l or "TWO verdicts" in l
             or "MISMATCHES" in l or "exceptions raised" in l]
    caught = any(not l.strip().endswith(": 0") and ": 0 " not in l for l in lines)
    # explicit: read the three numbers rather than trusting the string test
    nums = {}
    for l in lines:
        k, _, v = l.partition(":")
        nums[k.strip()] = int(v.strip().split()[0])
    caught = any(v > 0 for k, v in nums.items() if "redundant" not in k)
    print("%-52s %s" % (label, "CAUGHT" if caught else ">>> NOT CAUGHT <<<"))
    for k, v in nums.items():
        print("      %-32s %d" % (k, v))
    if not caught:
        fail += 1
print()
print("planted defects: %d, caught: %d, MISSED: %d" % (len(DEFECTS), len(DEFECTS) - fail, fail))
print("50-partition.py has now been seen to FAIL, so its 0/0/0 on the shipped tree is a")
print("measurement rather than a hope (P-22).")
sys.exit(1 if fail else 0)
