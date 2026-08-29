#!/usr/bin/env python3
"""T456 -- C-T449-5 ATTACKED: does the wall-clock bound demote work that the count cap
would have refused?

T451 replaced `MAX_REFS_PROBED = 8` with `REF_PROBE_SECONDS = 6.0` and argued the new
bound "can only fire far outside the measured population (max fan-out 2 vs a 6-second
ceiling at ~0.1 s per ref)".  That argument is about the COUNT axis.  The new bound is on
the TIME axis, and on the time axis a fan-out of 2 is not far outside anything: it needs
ONE slow probe, not eight refs.

This instrument makes the host slow -- not the code -- by pointing the module's `GIT` at
a wrapper that sleeps before exec'ing the real git.  Nothing about the predicate is
stubbed or patched; the only change is how long git takes to answer, which is exactly the
variable a loaded CI box moves.

FIXTURE: HLOAD/T955 -- two name-matching refs (the MEASURED maximum fan-out on the live
repo), the only carrier SECOND in sort order, task branch absent.

  RED   (MAX_REFS_PROBED=8) probes both regardless of the clock -> carrier found -> REFUSE
  GREEN (REF_PROBE_SECONDS) stops after the first slow probe    -> carrier UNPROBED

If GREEN demotes where RED refuses, the change has a state that moved in the
work-destroying direction, and the handoff's "nothing that refused before demotes now" is
true only of a fast host.

usage: 12-clock.py <red.py> <green.py> <fixture-dir> <workdir> [sleep-secs]
"""
import importlib.util
import os
import stat
import sys
import time

RED, GREEN, FIX, WORK = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
SLEEP = float(sys.argv[5]) if len(sys.argv) > 5 else 3.5
os.makedirs(WORK, exist_ok=True)

import shutil
REALGIT = shutil.which("git")
if not REALGIT:
    sys.exit("ABORT: no git on PATH -- nothing measured")
SLOW = os.path.join(WORK, "slowgit")
with open(SLOW, "w", encoding="utf-8") as fh:
    fh.write("#!/bin/sh\nsleep %s\nexec %s \"$@\"\n" % (SLEEP, REALGIT))
os.chmod(SLOW, os.stat(SLOW).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# PROVE THE WRAPPER IS ACTUALLY SLOW before believing any verdict taken through it.
import subprocess
t0 = time.monotonic()
p = subprocess.run([SLOW, "-C", FIX, "rev-parse", "HEAD"], capture_output=True, text=True)
dt = time.monotonic() - t0
if p.returncode != 0 or dt < SLEEP:
    sys.exit("ABORT: the slow-git wrapper did not work (rc=%s, %.2fs < %.2fs). Every "
             "'unprobed' below would be an artefact of a wrapper that never slept."
             % (p.returncode, dt, SLEEP))
print("slow-git wrapper : %s   (sleeps %.1fs; measured one call at %.2fs)"
      % (SLOW, SLEEP, dt))


def load(path, name, slow):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if getattr(m, "branch_sweep", "x") is None:
        sys.exit("ABORT: %s could not import branch_sweep" % path)
    m.set_repo(FIX)
    if slow:
        m.GIT = SLOW
    return m


BRANCH = "softhouse/T955-decoy-target"   # absent -- the `_absent_verdict` leg
TID = "T955"

print("case             : HLOAD/%s, recorded branch %s (absent)" % (TID, BRANCH))
print("refs naming it   : softhouse/aaa-t955-decoy (name-only, sorts FIRST),")
print("                   softhouse/zzz-t955-carrier (CARRIES, sorts SECOND)")
print()
results = {}
for slow in (False, True):
    for tag, path in (("RED  ", RED), ("GREEN", GREEN)):
        m = load(path, "m_%s_%s" % (tag.strip(), slow), slow)
        m._MAINTREE = ("uncached", None)
        m._REF_INDEX = ("uncached", None)
        m._IDPAT = {}
        t = time.monotonic()
        kind, text = m.branch_wip(BRANCH, TID)
        action = m.reconcile_action(kind)
        el = time.monotonic() - t
        pol = "REFUSE" if action.startswith("REFUSE") else "demote"
        results[(tag.strip(), slow)] = (kind, pol)
        print("%-6s host=%-6s  %-18s %-7s   (%.1fs wall)"
              % (tag, "SLOW" if slow else "fast", kind, pol, el))
        low = text.lower()
        for needle in ("not probed", "ref_probe_seconds", "ceiling"):
            i = low.find(needle)
            if i >= 0:
                print("        note> ...%s..." % text[max(0, i - 90):i + 150]
                      .replace("\n", " "))
                break
    print()

print("=" * 84)
rf, gf = results[("RED", False)][1], results[("GREEN", False)][1]
rs, gs = results[("RED", True)][1], results[("GREEN", True)][1]
print("fast host : RED %-7s  GREEN %-7s" % (rf, gf))
print("SLOW host : RED %-7s  GREEN %-7s" % (rs, gs))
print()
if rs == "REFUSE" and gs == "demote":
    print("FINDING: on a SLOW host GREEN DEMOTES a task RED REFUSES to demote.")
    print("         The count cap could not truncate a 2-ref population; the wall-clock")
    print("         bound can. That is a state that moved in the WORK-DESTROYING")
    print("         direction, and it is invisible to the 288-state partition because")
    print("         the partition stubs `refs_carrying_content` -- the very function")
    print("         whose truncation rule changed.")
    sys.exit(1)
if gs == gf:
    print("NO FINDING: GREEN's verdict did not move with the clock at sleep=%.1fs."
          % SLEEP)
    print("            This is a statement about THIS sleep value, not about the world.")
sys.exit(0)
