#!/usr/bin/env python3
"""T469 / CLAIM 3b -- WHO IS RIGHT ABOUT `timeout=15`?

The task brief filed `timeout=15` as a DEFECT ("2.5x the whole probe's 6.0 s ceiling").
T462 refuses to tighten it and calls the refusal a derived conclusion: every second cut
off it converts a slow-but-SUCCESSFUL probe into rc=None -> `unprobed` -> DEMOTE, i.e.
it breaks the subset guarantee in the DESTRUCTIVE direction.

Driven, not argued.  Variant GREEN-T3 is GREEN with `ref_content_evidence`'s two
per-call timeouts tightened 15 -> 3, both sites asserted unique before writing.  The
host is slowed to 4.0 s/call, i.e. slower than the tightened timeout and faster than
the shipped one -- the exact band in which the two differ.

Expected if T462 is right:  GREEN REFUSES, GREEN-T3 DEMOTES the same evidence.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.abspath(sys.argv[1])
FIX = os.path.abspath(sys.argv[2])
SLEEP = sys.argv[3] if len(sys.argv) > 3 else "4.0"
REALGIT = subprocess.run(["/usr/bin/which", "git"], capture_output=True,
                         text=True).stdout.strip()
WRAP = os.path.join(HERE, "gitwrap.sh")

src = open(os.path.join(V, "green.py")).read()
N1 = 'rc, out, err = _run([GIT, "log", "--format=%H%x09%s", "main..%s" % ref], timeout=15)'
N2 = 'rc2, out2, err2 = _run([GIT, "diff", "--name-only", "main...%s" % ref], timeout=15)'
for n in (N1, N2):
    if src.count(n) != 1:
        sys.exit("REFUSING TO PLANT: %r matched %d sites" % (n[:40], src.count(n)))
t3 = os.path.join(V, "green_timeout3.py")
open(t3, "w").write(src.replace(N1, N1.replace("timeout=15", "timeout=3"))
                       .replace(N2, N2.replace("timeout=15", "timeout=3")))
w = open(t3).read()
assert w.count("timeout=3)") == 2, "plant did not take"
assert N1 not in w and N2 not in w, "the two ref_content_evidence sites survived"
print("NOTE: `timeout=15` has 5 call sites in this file; only the 2 inside\n"
      "ref_content_evidence are tightened here -- the other 3 are on the landed-work\n"
      "path and are NOT what either T456 or T462 is arguing about.")
print("GREEN-T3 planted (both per-call timeouts 15 -> 3); sites UNIQUE; plant LIVE\n")


def run(mod, label):
    env = dict(os.environ)
    env.update(T469_REALGIT=REALGIT, T469_SLEEP=SLEEP, T469_GITLOG="")
    p = subprocess.run([sys.executable, os.path.join(HERE, "_one.py"), mod, FIX,
                        "softhouse/T900-work", "T900", WRAP, "0"],
                       capture_output=True, text=True, env=env)
    if p.returncode != 0:
        print("%-12s ERROR %s" % (label, p.stderr[-300:]))
        return None
    r = json.loads(p.stdout)
    print("%-12s %-18s %-8s  wall=%ss" % (label, r["kind"], r["polarity"], r["wall"]))
    return r


print("case F2: fan-out 2, carrier SECOND, branch pruned; host = %s s/git call\n" % SLEEP)
print("%-12s %-18s %-8s" % ("variant", "kind", "polarity"))
a = run(os.path.join(V, "cap8.py"), "CAP8")
b = run(os.path.join(V, "green.py"), "GREEN")
c = run(t3, "GREEN-T3")
print()
if b and c and b["polarity"] == "REFUSE" and c["polarity"] == "demote":
    print("TIGHTENING timeout=15 IS DESTRUCTIVE: the same evidence that GREEN REFUSES")
    print("to demote is DEMOTED once the per-call timeout is cut. T462's refusal to")
    print("tighten it is CORRECT and is a conclusion, not an omission.")
    sys.exit(0)
print("NOT REPRODUCED at this sleep -- T462's conclusion is NOT established by this run.")
sys.exit(1)
