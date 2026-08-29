#!/usr/bin/env python3
"""Repeat the shared-budget break N times: a one-off in a timing experiment is noise."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V, FIX, OUT, SLEEP, D, N = (os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]),
                            os.path.abspath(sys.argv[3]), sys.argv[4], sys.argv[5],
                            int(sys.argv[6]))
REALGIT = subprocess.run(["/usr/bin/which", "git"], capture_output=True,
                         text=True).stdout.strip()
WRAP = os.path.join(HERE, "gitwrap.sh")
PP = "log --format=%H%x09%s main..refs/heads/softhouse/"


def run(variant):
    gl = os.path.join(OUT, "rep-gitlog.txt")
    if os.path.exists(gl):
        os.remove(gl)
    env = dict(os.environ)
    env.update(T469_REALGIT=REALGIT, T469_GITLOG=gl, T469_SLEEP=SLEEP)
    p = subprocess.run([sys.executable, os.path.join(HERE, "_two.py"),
                        os.path.join(V, variant), FIX, "softhouse/T920-work", "T920",
                        "softhouse/T900-work", "T900", WRAP, D],
                       capture_output=True, text=True, env=env)
    r = json.loads(p.stdout)
    lines = open(gl).read().splitlines() if os.path.exists(gl) else []
    r["sink"] = sum(1 for l in lines if l.startswith(PP + "s"))
    r["vict"] = sum(1 for l in lines if l.startswith(PP + "aaa-T900")
                    or l.startswith(PP + "zzz-T900"))
    return r


print("sleep=%ss/call  %d repeats per deadline" % (SLEEP, N))
print("%-6s %-7s %-6s %-6s %-9s %-16s %-8s"
      % ("dline", "variant", "sink", "vict", "sinkwall", "victim kind", "polarity"))
brk = 0
DL = [float(x) for x in D.split(",")]
for D in DL:
  D = str(D)
  for i in range(N):
    got = {}
    for name, f in (("CAP8", "cap8.py"), ("GREEN", "green.py")):
        r = run(f)
        got[name] = r
        print("%-6s %-7s %-6d %-6d %-9s %-16s %-8s"
              % (D, name, r["sink"], r["vict"], r["sink_wall"], r["victim_kind"],
                 r["victim_polarity"]))
    if got["CAP8"]["victim_polarity"] == "REFUSE" and got["GREEN"]["victim_polarity"] == "demote":
        print("       ^^ BREAK -- the count cap REFUSES, the floored code DEMOTES")
        brk += 1
print("\nbreaks: %d over %d cells" % (brk, N * len(DL)))
