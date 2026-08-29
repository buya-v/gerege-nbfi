#!/usr/bin/env python3
"""T469 -- ATTACK ON THE SUBSET GUARANTEE AS STATED.

T462 states the guarantee as:

    the set of refs this probe leaves UNPROBED is a SUBSET of the set the count cap
    it replaced would have left unprobed, ON EVERY HOST AND EVERY BUDGET.

The budget is NOT per-probe.  `--deadline-secs` installs ONE process-global DEADLINE
(set_deadline sets a module global; _run reads it for every call), and the resolver
walks EVERY in_progress task inside that one process.  So a task whose probe consumes
MORE of the shared budget under the floored code than under the count cap can starve a
LATER task's probe into rc=None -> `unprobed` -> DEMOTE.

Construction:
  SINK   T920, fan-out 20, all name-only, branch pruned.
         CAP8 probes 8 refs (16 git calls).  GREEN probes until the 6.0s ceiling, so on
         a host at ~0.15 s/call it probes all 20 (40 git calls).
  VICTIM T900, fan-out 2, carrier SECOND, branch pruned.  MUST REFUSE.

Both are reconciled in ONE process under ONE budget, sink first -- exactly the shape
`ready-tasks.py --reconcile --deadline-secs N` produces.
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

PROBE_PREFIX = "log --format=%H%x09%s main.."


def run(variant, deadline):
    gitlog = os.path.join(OUT, "budget-gitlog.txt")
    if os.path.exists(gitlog):
        os.remove(gitlog)
    env = dict(os.environ)
    env.update(T469_REALGIT=REALGIT, T469_GITLOG=gitlog, T469_SLEEP=SLEEP)
    p = subprocess.run([sys.executable, os.path.join(HERE, "_two.py"),
                        os.path.join(V, variant), FIX,
                        "softhouse/T920-work", "T920",
                        "softhouse/T900-work", "T900",
                        WRAP, str(deadline)],
                       capture_output=True, text=True, env=env)
    if p.returncode != 0:
        return {"ERROR": p.stderr[-600:]}
    r = json.loads(p.stdout)
    lines = open(gitlog).read().splitlines() if os.path.exists(gitlog) else []
    r["git_calls"] = len(lines)
    r["sink_probes"] = sum(1 for l in lines if l.startswith(PROBE_PREFIX + "refs/heads/softhouse/s"))
    r["victim_probes"] = sum(1 for l in lines
                             if l.startswith(PROBE_PREFIX + "refs/heads/softhouse/aaa-T900")
                             or l.startswith(PROBE_PREFIX + "refs/heads/softhouse/zzz-T900"))
    return r


print("sleep/call = %ss ; sink T920 fan-out 20 ; victim T900 fan-out 2 carrier 2nd" % SLEEP)
print()
print("%-8s %-9s | %-9s %-9s | %-16s %-8s %-8s"
      % ("deadline", "variant", "sinkprobe", "victprobe", "victim kind", "polarity", "wall"))
broke = 0
for d in (3.0, 4.0, 5.0, 6.0, 8.0, 12.0, 30.0):
    row = {}
    for variant, name in (("cap8.py", "CAP8"), ("green.py", "GREEN"), ("red.py", "RED")):
        r = run(variant, d)
        if "ERROR" in r:
            print("%-8s %-9s | ERROR %s" % (d, name, r["ERROR"]))
            continue
        row[name] = r
        print("%-8s %-9s | %-9d %-9d | %-16s %-8s %-8s"
              % (d, name, r["sink_probes"], r["victim_probes"], r["victim_kind"],
                 r["victim_polarity"], r["victim_wall"]))
    a, b = row.get("CAP8"), row.get("GREEN")
    if a and b and a["victim_polarity"] == "REFUSE" and b["victim_polarity"] == "demote":
        print("         ^^^^ SUBSET GUARANTEE BROKEN AT THIS BUDGET: the count cap "
              "REFUSES, the floored code DEMOTES")
        broke += 1
    print()

print("budgets at which GREEN destroys work the count cap preserved: %d" % broke)
sys.exit(1 if broke else 0)
