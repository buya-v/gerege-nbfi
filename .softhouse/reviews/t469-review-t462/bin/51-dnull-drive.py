#!/usr/bin/env python3
"""T469 -- is T462's NEGATIVE CONTROL (D-NULL) really behaviour-preserving?

T462's `50-expected-verdicts.py` requires D-NULL -- swapping the two unconditional
probe calls at the top of `_absent_verdict` -- to stay GREEN on every arm, and reports
"3 planted, 2 caught, 1 CORRECTLY IGNORED".  The two swapped calls are:

    ev, complete, ev_note = landed_evidence(tid)
    carriers, ... = refs_carrying_content(tid, branch)

They share ONE wall-clock budget (`_run` -> `_remaining()` -> `--deadline-secs`), so
their ORDER decides which of them gets starved.  If that is so, the swap is not
behaviour-preserving and the "negative control" is a third DEFECT that went uncaught --
and it is the SAME class as C-T456-1, the finding this branch exists to fix.

The plant is made on GREEN's own bytes and its uniqueness is asserted before writing.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.abspath(sys.argv[1])
FIX = os.path.abspath(sys.argv[2])
OUT = os.path.abspath(sys.argv[3])
SLEEP = sys.argv[4]
os.makedirs(OUT, exist_ok=True)
REALGIT = subprocess.run(["/usr/bin/which", "git"], capture_output=True,
                         text=True).stdout.strip()
WRAP = os.path.join(HERE, "gitwrap.sh")

src = open(os.path.join(V, "green.py")).read()
NEEDLE = ("    ev, complete, ev_note = landed_evidence(tid)\n"
          "    carriers, name_only, unprobed, mentions, ref_note = "
          "refs_carrying_content(tid, branch)\n")
SWAP = ("    carriers, name_only, unprobed, mentions, ref_note = "
        "refs_carrying_content(tid, branch)\n"
        "    ev, complete, ev_note = landed_evidence(tid)\n")
if src.count(NEEDLE) != 1:
    sys.exit("REFUSING TO PLANT: the D-NULL site occurs %d times, not 1" % src.count(NEEDLE))
dnull = os.path.join(V, "green_dnull.py")
open(dnull, "w").write(src.replace(NEEDLE, SWAP))
w = open(dnull).read()
assert SWAP in w and NEEDLE not in w, "plant did not take"
print("D-NULL planted on GREEN's bytes; site UNIQUE; plant verified LIVE\n")


def run(mod, deadline):
    env = dict(os.environ)
    env.update(T469_REALGIT=REALGIT, T469_SLEEP=SLEEP, T469_GITLOG="")
    p = subprocess.run([sys.executable, os.path.join(HERE, "_one.py"), mod, FIX,
                        "softhouse/T930-work", "T930", WRAP, str(deadline)],
                       capture_output=True, text=True, env=env)
    if p.returncode != 0:
        return {"ERROR": p.stderr[-400:]}
    return json.loads(p.stdout)


print("case: T930's work IS ON MAIN (landed_evidence => `merged`, a REFUSAL);")
print("      6 further refs merely NAME T930, so the ref probe has budget to spend.")
print("      Branch pruned, so this is _absent_verdict -- the arm D-NULL edits.\n")
print("%-10s %-14s %-20s %-9s" % ("deadline", "variant", "kind", "polarity"))
broke = 0
for d in (0.4, 0.6, 0.9, 1.2, 2.0, 5.0, 30.0):
    got = {}
    for name, mod in (("GREEN", os.path.join(V, "green.py")), ("GREEN+D-NULL", dnull)):
        r = run(mod, d)
        if "ERROR" in r:
            print("%-10s %-14s ERROR %s" % (d, name, r["ERROR"]))
            continue
        got[name] = r
        print("%-10s %-14s %-20s %-9s" % (d, name, r["kind"], r["polarity"]))
    a, b = got.get("GREEN"), got.get("GREEN+D-NULL")
    if a and b and a["polarity"] == "REFUSE" and b["polarity"] == "demote":
        print("           ^^^^ D-NULL IS NOT BEHAVIOUR-PRESERVING: it flips "
              "REFUSE -> demote at this budget")
        broke += 1
    print()
print("budgets at which the 'negative control' destroys work: %d" % broke)
sys.exit(1 if broke else 0)
