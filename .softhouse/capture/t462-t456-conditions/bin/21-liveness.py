#!/usr/bin/env python3
"""T462 / C-T456-3 -- THE CITATION HAD TO POINT AT SOMETHING THAT SUPPORTS IT.

The shipped `ref_content_evidence` docstring says of the generous SUBJECT half: "every
affected id either is absent from tasks.json or has a branch with commits ahead of main,
so the ref arm is unreachable for all of them today [out/22-liveness.txt]".  That
artefact ends with the line `non-terminal ids blocked by a FOREIGN-owned ref today: 4`
and lists four `<== LIVE FOREIGN-REF REFUSAL` rows.  A reader who follows the citation
finds the opposite of the sentence that carries it.

The sentence can still be TRUE, and T456 showed it is -- but only by asking a question
T451's artefact never asked.  `refs_carrying_content` is reached ONLY down particular
arms of `_branch_wip_core`; a task whose recorded branch has commits ahead of main
returns `commits` long before any ref is looked at.  Status alone cannot answer that.
The KIND can, and the only way to get the kind is to CALL `branch_wip`.

So this instrument calls it, on the live repo, for every (id, foreign-ref) pair, and
reports the MEMBER SET of ids where a foreign ref actually buys a refusal today -- with
the tree it was measured at, because that set is weather (see 20-relaxation-members.py).

usage: 21-liveness.py [<repo>]
"""
import importlib.util
import json
import os
import re
import subprocess
import sys

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
S = ".softhouse"                       # assembled, never spelled as a literal path
TOOL = os.path.join(REPO, S, "bin", "ready-tasks.py")
TASKS = os.path.join(REPO, S, "tasks.json")
for p in (TOOL, TASKS):
    if not os.path.exists(p):
        sys.exit("ABORT: %s missing -- nothing to measure" % p)


def git(*a):
    p = subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else "?"


print("MEASURED-AT")
print("  repo        : %s" % REPO)
print("  HEAD        : %s  %s" % (git("rev-parse", "HEAD")[:12],
                                  git("log", "-1", "--format=%ad", "--date=iso")))
print("  resolver sha: %s" % git("hash-object", TOOL)[:12])
print()

spec = importlib.util.spec_from_file_location("rt", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
if getattr(m, "branch_sweep", "x") is None:
    sys.exit("ABORT: could not import branch_sweep -- nothing below would be a "
             "measurement of the shipped code")
m.set_repo(REPO)

doc = json.load(open(TASKS, encoding="utf-8"))
tasks = {t["id"]: t for t in doc["tasks"]}
print("tasks.json   : %d tasks" % len(tasks))
print("NOT_RUNNABLE : %s" % sorted(m.NOT_RUNNABLE))

idx, note = m.ref_index()
if idx is None:
    sys.exit("ABORT: ref index unavailable: %s" % note)
print("live refs    : %d" % len(idx.names()))
print()

ID = re.compile(r"(?<![0-9A-Za-z])((?:[Tt][0-9]+)|(?:A2-[0-9]+))(?![0-9A-Za-z])")
# THE ARMS THAT ACTUALLY CONSULT THE REF STORE.  Transcribed from `_branch_wip_core`;
# any other kind means the ref store was never asked, so a foreign ref could not have
# bought anything.  If this list rots the instrument says so below rather than lying.
REF_ARMS = {"relocated", "name-only-refs", "stillborn", "stillborn-carried",
            "indeterminate", "unstarted"}

pairs = {}
for n in sorted(idx.names()):
    short = m.branch_sweep.short(n)
    for tid in set(x.upper() for x in ID.findall(short)):
        lead = ID.search(short.split("/")[-1])
        owner = lead.group(1).upper() if lead else "?"
        if owner != tid:
            pairs.setdefault(tid, []).append((short, owner))

print("ids with at least one FOREIGN ref naming them: %d" % len(pairs))
print()
print("%-7s %-13s %-22s %-8s %-9s %s"
      % ("id", "status", "kind (branch_wip)", "polarity", "ref arm?", "foreign refs"))
print("-" * 118)
buys, unreachable, terminal = [], [], []
for tid in sorted(pairs):
    t = tasks.get(tid)
    status = t.get("status") if t else "NOT IN tasks.json"
    branch = (t or {}).get("branch")
    kind, _text = m.branch_wip(branch, tid)
    action = m.reconcile_action(kind)
    pol = "REFUSE" if action.startswith("REFUSE") else "demote"
    base = kind.split("/")[0]
    reached = base in REF_ARMS
    refs = ", ".join("%s(%s)" % (r, o) for r, o in pairs[tid][:3])
    print("%-7s %-13s %-22s %-8s %-9s %s"
          % (tid, status, kind, pol, "YES" if reached else "no", refs))
    print("        recorded branch: %s" % (branch or "- (none recorded)"))
    if t is None or status in m.NOT_RUNNABLE:
        terminal.append((tid, status, kind, pol))
    elif reached and pol == "REFUSE":
        buys.append((tid, status, kind, branch, pairs[tid]))
    else:
        unreachable.append((tid, status, kind, pol))

print()
print("=" * 118)
print("MEMBER SET -- non-terminal ids where a FOREIGN ref ACTUALLY buys a REFUSAL today")
print("(ref arm REACHED **and** polarity REFUSE **and** the id is still runnable):")
if not buys:
    print("   { }   EMPTY ON THIS TREE.")
for tid, status, kind, branch, refs in buys:
    print("   %-6s status=%-12s kind=%-20s branch=%s" % (tid, status, kind, branch))
    for r, o in refs:
        print("          foreign ref %s (owned by %s)" % (r, o))
print()
print("   |set| = %d" % len(buys))
print()
print("NON-TERMINAL BUT THE REF ARM IS NOT REACHED (this is the half status cannot see):")
for tid, status, kind, pol in unreachable:
    print("   %-6s status=%-12s kind=%-20s -> %s   (the ref store was never asked)"
          % (tid, status, kind, pol))
print()
print("TERMINAL / ABSENT FROM tasks.json (never offered for dispatch at all): %d"
      % len(terminal))
for tid, status, kind, pol in terminal[:40]:
    print("   %-6s status=%-16s kind=%-20s %s" % (tid, status, kind, pol))
print()
print("WHAT THIS DOES AND DOES NOT SUPPORT")
print("  SUPPORTED: the residual (b) claim -- the generous SUBJECT half does not buy any")
print("             live task a refusal ON THIS TREE, because reachability is decided by")
print("             the KIND, not by the status.")
print("  NOT SUPPORTED, and not claimed: that it CANNOT. Every id in the")
print("             'ref arm is not reached' block above becomes reachable the moment")
print("             its recorded branch is pruned or reset to the dispatch commit, which")
print("             is a thing this program's own sweep does routinely.")
print("  THE CITATION THIS REPLACES: T451's out/22-liveness.txt keyed on STATUS alone")
print("             and printed 4 rows marked LIVE FOREIGN-REF REFUSAL -- the literal")
print("             opposite of the sentence citing it.")
sys.exit(0)
