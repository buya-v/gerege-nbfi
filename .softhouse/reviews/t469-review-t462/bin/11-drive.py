#!/usr/bin/env python3
"""T469 -- re-derivation of T462's CLAIM 1/2/3, on my own fixture, my own instruments.

Every cell is a fresh interpreter.  The HOST is slowed with a wrapper on GIT; nothing
in the predicate is edited, stubbed or monkeypatched.  Probe counts are read from the
WRAPPER'S OWN LOG, i.e. measured on the host side, so a module that lied in its note
could not move them.

LIVENESS IS PROVED BEFORE ANY VERDICT IS BELIEVED: the slow leg asserts that the
wrapper actually slept (wall / calls >= sleep) and that the fast leg did not.
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.abspath(sys.argv[1])     # variants dir
FIX = os.path.abspath(sys.argv[2])   # fixture repo
OUT = os.path.abspath(sys.argv[3])   # scratch out dir -- ABSOLUTE: the wrapper runs with cwd=fixture
SLEEP = sys.argv[4] if len(sys.argv) > 4 else "3.2"
ONLY = sys.argv[5].split(",") if len(sys.argv) > 5 else None

os.makedirs(OUT, exist_ok=True)
REALGIT = subprocess.run(["/usr/bin/which", "git"], capture_output=True,
                         text=True).stdout.strip()
WRAP = os.path.join(HERE, "gitwrap.sh")
os.chmod(WRAP, 0o755)

CASES = [
    # label, branch, tid, fanout, carrier index (0-based), what the case is for
    ("F2",  "softhouse/T900-work", "T900", 2, 1, "fan-out 2, carrier 2nd, branch PRUNED -> _absent_verdict"),
    ("F2S", "softhouse/T901-work", "T901", 2, 1, "fan-out 2, carrier 2nd, branch STANDING -> stillborn-carried"),
    ("F8",  "softhouse/T908-work", "T908", 8, 7, "fan-out 8, carrier 8th (index 7) -- THE FLOOR BOUNDARY"),
    ("F9",  "softhouse/T909-work", "T909", 9, 8, "fan-out 9, carrier 9th (index 8) -- OUTSIDE the floor"),
    ("F1",  "softhouse/T910-work", "T910", 1, 0, "fan-out 1, carrier 1st -- MUST-REFUSE control"),
    ("N",   "softhouse/T911-work", "T911", 2, None, "fan-out 2, NO carrier -- MUST-DEMOTE control"),
]
VARIANTS = [("CAP8", "cap8.py"), ("RED", "red.py"), ("GREEN", "green.py")]
PROBE = re.compile(r"^log --format=%H%x09%s main\.\.")


def cell(variant_file, case, slow, deadline="0"):
    gitlog = os.path.join(OUT, "gitlog.txt")
    if os.path.exists(gitlog):
        os.remove(gitlog)
    env = dict(os.environ)
    env["T469_REALGIT"] = REALGIT
    env["T469_GITLOG"] = gitlog
    env["T469_SLEEP"] = SLEEP if slow else "0"
    label, branch, tid = case[0], case[1], case[2]
    t0 = time.monotonic()
    p = subprocess.run([sys.executable, os.path.join(HERE, "_one.py"),
                        os.path.join(V, variant_file), FIX, branch, tid, WRAP,
                        deadline],
                       capture_output=True, text=True, env=env)
    wall = time.monotonic() - t0
    if p.returncode != 0:
        return {"ERROR": p.stderr[-800:]}
    r = json.loads(p.stdout)
    lines = open(gitlog).read().splitlines() if os.path.exists(gitlog) else []
    r["git_calls"] = len(lines)
    r["probed"] = sum(1 for l in lines if PROBE.match(l))
    r["outer_wall"] = round(wall, 2)
    return r


def main():
    # ---------- LIVENESS OF THE HOST WRAPPER, before any verdict is believed ----------
    sl = float(SLEEP)
    fast = cell("red.py", CASES[0], slow=False)
    slow = cell("red.py", CASES[0], slow=True)
    per_fast = fast["outer_wall"] / max(fast["git_calls"], 1)
    per_slow = slow["outer_wall"] / max(slow["git_calls"], 1)
    print("HOST LIVENESS  real git = %s ; wrapper = %s ; sleep = %ss" % (REALGIT, WRAP, SLEEP))
    print("  fast leg: %d git calls in %.2fs  -> %.3fs/call" % (fast["git_calls"], fast["outer_wall"], per_fast))
    print("  SLOW leg: %d git calls in %.2fs  -> %.3fs/call" % (slow["git_calls"], slow["outer_wall"], per_slow))
    if per_slow < sl:
        sys.exit("REFUSING TO REPORT: the SLOW wrapper did not actually sleep "
                 "(%.3fs/call < %ss). An 'unprobed' I did not cause is not evidence." % (per_slow, sl))
    if per_fast > sl / 2:
        sys.exit("REFUSING TO REPORT: the FAST leg is not fast (%.3fs/call)." % per_fast)
    if fast["git_calls"] == 0 or slow["git_calls"] == 0:
        sys.exit("REFUSING TO REPORT: the wrapper's argv LOG is empty, so every probe "
                 "count below would be a fabricated 0.")
    print("  wrapper PROVED live: slow/fast = %.1fx ; argv log CAPTURING (%d/%d calls)\n"
          % (per_slow / max(per_fast, 1e-6), fast["git_calls"], slow["git_calls"]))

    rows = []
    for case in CASES:
        if ONLY and case[0] not in ONLY:
            continue
        print("=" * 100)
        print("CASE %-4s  %s" % (case[0], case[5]))
        print("%-6s %-6s | %-22s %-8s %-7s %-8s" % ("host", "variant", "kind", "polarity", "probed", "wall"))
        for host in ("fast", "SLOW"):
            for vname, vfile in VARIANTS:
                r = cell(vfile, case, slow=(host == "SLOW"))
                if "ERROR" in r:
                    print("  %-6s %-6s | ERROR %s" % (host, vname, r["ERROR"]))
                    continue
                print("  %-6s %-6s | %-22s %-8s %-7d %-8s"
                      % (host, vname, r["kind"], r["polarity"], r["probed"], r["outer_wall"]))
                rows.append(dict(case=case[0], host=host, variant=vname, **r))
        print()

    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    # ---------------- ADJUDICATION, computed rather than eyeballed ----------------
    def get(c, h, v):
        for r in rows:
            if r["case"] == c and r["host"] == h and r["variant"] == v:
                return r
        return None

    print("=" * 100)
    fails = 0
    print("LEG 1 -- REGRESSION vs the count cap: any cell where CAP8 REFUSES and X demotes")
    for c in {r["case"] for r in rows}:
        for h in ("fast", "SLOW"):
            a = get(c, h, "CAP8")
            for v in ("RED", "GREEN"):
                b = get(c, h, v)
                if not a or not b:
                    continue
                if a["polarity"] == "REFUSE" and b["polarity"] == "demote":
                    mark = "<== WORK-DESTROYING REGRESSION"
                    print("  %-4s %-5s CAP8=REFUSE  %-5s=demote   %s" % (c, h, v, mark))
                    if v == "GREEN":
                        fails += 1

    print("\nLEG 2 -- SUBSET: probed(X) >= probed(CAP8) in every cell")
    bad = 0
    for r in rows:
        a = get(r["case"], r["host"], "CAP8")
        if a and r["variant"] != "CAP8" and r["probed"] < a["probed"]:
            print("  %-4s %-5s %-5s probed %d < CAP8 %d  <== SUBSET BROKEN"
                  % (r["case"], r["host"], r["variant"], r["probed"], a["probed"]))
            if r["variant"] == "GREEN":
                bad += 1
    print("  GREEN cells violating the subset property: %d" % bad)

    print("\nLEG 3 -- fast-host behaviour of GREEN identical to RED (kind AND polarity)")
    diff = 0
    for c in {r["case"] for r in rows}:
        a, b = get(c, "fast", "RED"), get(c, "fast", "GREEN")
        if a and b and (a["kind"], a["polarity"]) != (b["kind"], b["polarity"]):
            print("  %-4s RED=%s/%s  GREEN=%s/%s  <== CLEAN-HOST BEHAVIOUR CHANGED"
                  % (c, a["kind"], a["polarity"], b["kind"], b["polarity"]))
            diff += 1
    print("  fast-host cells where GREEN differs from RED: %d" % diff)

    print("\nLEG 4 -- 'A REVERT IS WRONG': cells where CAP8 demotes and RED/GREEN REFUSE")
    for c in {r["case"] for r in rows}:
        for h in ("fast", "SLOW"):
            a = get(c, h, "CAP8")
            b = get(c, h, "GREEN")
            if a and b and a["polarity"] == "demote" and b["polarity"] == "REFUSE":
                print("  %-4s %-5s CAP8=demote GREEN=REFUSE  <== reverting to the count "
                      "cap re-opens this" % (c, h))

    sys.exit(1 if (fails or bad or diff) else 0)


main()
