#!/usr/bin/env python3
"""T462 / C-T456-1 -- RE-DERIVED, not inherited.  Does a wall-clock bound demote work
that the count cap it replaced would have refused, and does a floor under the ceiling
close that?

THREE VARIANTS, and the third is the control T456 did not have:

  CAP8  the bound T451 REMOVED, reconstructed from RED by a textual transform whose
        liveness is proved below: MAX_REFS_PROBED = 8 and the clock arm disabled.
        This is the thing the new bound has to be no worse than.
  RED   main's shipped bytes: REF_PROBE_SECONDS = 6.0, no floor.
  GREEN this tree: the same ceiling with MIN_REFS_ALWAYS_PROBED under it.

TWO HOSTS.  `fast` is this machine.  `SLOW` points the module's GIT at a wrapper that
sleeps before exec'ing the real git.  NOTHING in the predicate is stubbed or patched --
the only variable moved is how long git takes to answer, which is what a loaded CI box
moves.  That is what makes T456's drive credible and it is why this one copies the
method and not the numbers.

WHAT WOULD FALSIFY THE FIX.  Two independent failures, both fatal here:
  (1) any case where CAP8 REFUSES on a SLOW host and GREEN demotes -- the floor did not
      restore the guarantee it was proposed to restore;
  (2) any case where RED and GREEN differ on a FAST host -- the floor changed the
      behaviour of the machine the driver actually runs on, which was not asked for.

usage: 11-clock.py <cap8-src> <red.py> <green.py> <fixture-dir> <workdir> [sleep-secs]
       (cap8-src is the file the CAP8 variant is DERIVED FROM -- normally red.py)
"""
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import time

CAP8SRC, RED, GREEN, FIX, WORK = sys.argv[1:6]
SLEEP = float(sys.argv[6]) if len(sys.argv) > 6 else 3.2
os.makedirs(WORK, exist_ok=True)

REALGIT = shutil.which("git")
if not REALGIT:
    sys.exit("ABORT: no git on PATH -- nothing measured")
SLOW = os.path.join(WORK, "slowgit")
with open(SLOW, "w", encoding="utf-8") as fh:
    fh.write("#!/bin/sh\nsleep %s\nexec %s \"$@\"\n" % (SLEEP, REALGIT))
os.chmod(SLOW, os.stat(SLOW).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# PROVE THE WRAPPER SLEEPS before believing any `unprobed` taken through it.  An
# instrument that reports truncation over a wrapper that never slept has measured its
# own staging.
t0 = time.monotonic()
p = subprocess.run([SLOW, "-C", FIX, "rev-parse", "HEAD"], capture_output=True, text=True)
dt = time.monotonic() - t0
if p.returncode != 0 or dt < SLEEP:
    sys.exit("ABORT: the slow-git wrapper did not work (rc=%s, %.2fs < %.2fs)."
             % (p.returncode, dt, SLEEP))
print("slow-git wrapper : %s   (sleeps %.2fs; one measured call took %.2fs)"
      % (SLOW, SLEEP, dt))

# ------------------------------------------------------------------ build CAP8 -------
# The pre-T451 bound, rebuilt by transform rather than by memory.  Both anchors are
# asserted UNIQUE first: a plant that silently no-ops turns this whole control into a
# duplicate of RED and every conclusion drawn from it into a tautology.
src = open(CAP8SRC, encoding="utf-8").read()
A_CAP = "MAX_REFS_PROBED = 512"
A_CLK = "        elif time.monotonic() - started > REF_PROBE_SECONDS:"
for anchor in (A_CAP, A_CLK):
    if src.count(anchor) != 1:
        sys.exit("ABORT: anchor %r occurs %d times in %s; refusing to build CAP8"
                 % (anchor, src.count(anchor), CAP8SRC))
cap8 = src.replace(A_CAP, "MAX_REFS_PROBED = 8")
cap8 = cap8.replace(A_CLK, "        elif False:   # CAP8: the clock arm did not exist")
if cap8 == src:
    sys.exit("ABORT: the CAP8 transform was a no-op. NOTHING WAS CONTROLLED FOR.")
CAP8 = os.path.join(WORK, "rt_cap8.py")
open(CAP8, "w", encoding="utf-8").write(cap8)
for name in ("branch_sweep.py",):
    s = os.path.join(os.path.dirname(os.path.abspath(RED)), name)
    if os.path.exists(s):
        shutil.copy(s, os.path.join(WORK, name))
print("CAP8 variant     : %s   (MAX_REFS_PROBED 512->8, clock arm disabled; %+d bytes)"
      % (CAP8, len(cap8) - len(src)))

# ------------------------------------------------------------------- the cases -------
# (label, tid, recorded branch, what the shape is)
CASES = [
    ("F2 ", "T801", "softhouse/T801-target", "fan-out 2, carrier 2nd, branch PRUNED"),
    ("F2S", "T802", "softhouse/T802-work",   "fan-out 2, carrier 2nd, branch STANDING"),
    ("F9 ", "T803", "softhouse/T803-target", "fan-out 9, carrier 9th, branch PRUNED"),
    ("F1 ", "T804", "softhouse/T804-target", "fan-out 1, carrier 1st, branch PRUNED"),
    ("N  ", "T805", "softhouse/T805-target", "fan-out 2, NO carrier,  branch PRUNED"),
]
# What each case MUST do when the probe is allowed to finish.  Absolute, written down
# before the run, so a variant that agrees with another variant for the wrong reason is
# still caught.
WANT_FAST = {"F2 ": "REFUSE", "F2S": "REFUSE", "F9 ": "REFUSE",
             "F1 ": "REFUSE", "N  ": "demote"}


def load(path, name, slow):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if getattr(m, "branch_sweep", "x") is None:
        sys.exit("ABORT: %s could not import branch_sweep -- every verdict would be an "
                 "artefact of my staging" % path)
    m.set_repo(FIX)
    if slow:
        m.GIT = SLOW
    # COUNT the probes without changing them: wrap, delegate, record.  This is
    # measurement, not stubbing -- the real function still decides every verdict.
    real = m.ref_content_evidence
    m._probe_count = [0]

    def counting(tid, ref, _r=real, _c=m._probe_count):
        _c[0] += 1
        return _r(tid, ref)
    m.ref_content_evidence = counting
    return m


VARIANTS = (("CAP8 ", CAP8), ("RED  ", RED), ("GREEN", GREEN))
res = {}
print()
print("%-6s %-6s %-4s %-22s %-8s %6s %8s" %
      ("var", "host", "case", "kind", "polarity", "probes", "wall"))
print("-" * 74)
for slow in (False, True):
    for tag, path in VARIANTS:
        m = load(path, "m_%s_%s" % (tag.strip(), slow), slow)
        for label, tid, branch, _shape in CASES:
            m._probe_count[0] = 0
            t = time.monotonic()
            try:
                kind, text = m.branch_wip(branch, tid)
                action = m.reconcile_action(kind)
            except Exception as exc:                                 # noqa: BLE001
                res[(tag.strip(), slow, label)] = ("EXCEPTION", "NONE", 0)
                print("%-6s %-6s %-4s %s: %s" % (tag, "SLOW" if slow else "fast",
                                                 label, type(exc).__name__, exc))
                continue
            el = time.monotonic() - t
            pol = ("REFUSE" if action.startswith("REFUSE")
                   else "demote" if action.startswith("demote") else "NONE")
            res[(tag.strip(), slow, label)] = (kind, pol, m._probe_count[0])
            print("%-6s %-6s %-4s %-22s %-8s %6d %7.1fs"
                  % (tag, "SLOW" if slow else "fast", label, kind, pol,
                     m._probe_count[0], el))
        print()

print("=" * 74)
print("LEG 1 -- FAST HOST: is the clean-host behaviour of GREEN identical to RED?")
print("=" * 74)
fast_drift = []
for label, tid, _b, shape in CASES:
    r = res[("RED", False, label)]
    g = res[("GREEN", False, label)]
    c = res[("CAP8", False, label)]
    ok = (r[0], r[1]) == (g[0], g[1])
    if not ok:
        fast_drift.append((label, r, g))
    want = WANT_FAST[label]
    print("  %s %-40s CAP8 %-7s RED %-7s GREEN %-7s  want %-7s %s"
          % (label, shape, c[1], r[1], g[1], want,
             "OK" if ok and g[1] == want else "<== DRIFT"))
    if g[1] != want:
        fast_drift.append((label, ("want", want, 0), g))

print()
print("=" * 74)
print("LEG 2 -- SLOW HOST: does GREEN demote anything CAP8 (the replaced bound) refuses?")
print("=" * 74)
worse_vs_cap8, worse_vs_red = [], []
for label, tid, _b, shape in CASES:
    c = res[("CAP8", True, label)]
    r = res[("RED", True, label)]
    g = res[("GREEN", True, label)]
    mark = ""
    if c[1] == "REFUSE" and g[1] == "demote":
        worse_vs_cap8.append((label, c, g))
        mark = "  <== GREEN DEMOTES WHAT THE OLD COUNT CAP REFUSED"
    if r[1] == "REFUSE" and g[1] == "demote":
        worse_vs_red.append((label, r, g))
    print("  %s %-40s CAP8 %-7s(%d) RED %-7s(%d) GREEN %-7s(%d)%s"
          % (label, shape, c[1], c[2], r[1], r[2], g[1], g[2], mark))

print()
print("PROBE-COUNT SUBSET CLAIM (the whole of the fix): on every case and every host,")
print("GREEN must probe AT LEAST as many refs as CAP8 did -- i.e. GREEN's truncated set")
print("is a SUBSET of CAP8's, so no truncation-caused REFUSE can become a demote.")
subset_viol = []
for slow in (False, True):
    for label, _t, _b, _s in CASES:
        c = res[("CAP8", slow, label)][2]
        g = res[("GREEN", slow, label)][2]
        if g < c:
            subset_viol.append((label, "SLOW" if slow else "fast", c, g))
        print("   %-4s host=%-4s  CAP8 probed %d, GREEN probed %d   %s"
              % (label, "SLOW" if slow else "fast", c, g,
                 "OK" if g >= c else "<== VIOLATION"))

print()
print("=" * 74)
bad = 0
if fast_drift:
    bad = 1
    print("FAIL: clean-host behaviour is not what it was / not what was wanted: %s"
          % fast_drift)
else:
    print("PASS: on a fast host every variant agrees with the written-down expectation,")
    print("      and GREEN's kind and polarity are identical to RED's on all %d cases."
          % len(CASES))
if worse_vs_cap8:
    bad = 1
    print("FAIL: GREEN demotes on a SLOW host where the REPLACED count cap refused: %s"
          % [x[0] for x in worse_vs_cap8])
else:
    print("PASS: no case where CAP8 refuses on a SLOW host and GREEN demotes.")
if subset_viol:
    bad = 1
    print("FAIL: GREEN probed FEWER refs than CAP8: %s" % subset_viol)
else:
    print("PASS: GREEN's probe count >= CAP8's on every case and both hosts.")
print()
print("STILL TRUE AND NOT CLAIMED OTHERWISE: cases where RED refuses on a SLOW host and")
print("GREEN demotes: %s -- and cases where BOTH CAP8 and GREEN demote on a SLOW host"
      % ([x[0] for x in worse_vs_red] or "none"))
print("are NOT fixed by a floor; they are the residual, and F9 is there to show one.")
sys.exit(bad)
