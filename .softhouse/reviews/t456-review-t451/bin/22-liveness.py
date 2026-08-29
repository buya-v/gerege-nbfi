#!/usr/bin/env python3
"""T456 -- is T451's residual (1) UNREACHABLE today, as its handoff says?

THE CLAIM UNDER TEST (T451 handoff, residual 1; and the same sentence in the shipped
docstring, `ref_content_evidence` note (b)):

    "every affected id is either absent from tasks.json or has a branch with commits
     ahead of main, so the ref arm is UNREACHABLE for all of them today
     [out/22-liveness.txt]"

T451's own cited artefact prints `non-terminal ids blocked by a FOREIGN-owned ref today:
4`, each flagged `<== LIVE FOREIGN-REF REFUSAL`, because its `reachable` predicate tests
only the FIRST disjunct (status not terminal) and never the second (commits ahead).  So
the artefact neither supports nor refutes the sentence -- it answers a different
question.

This instrument settles it the only way that is not a paraphrase: it CALLS `branch_wip`
on the live repo for every affected id and reports which arm actually fires.  The ref arm
is reached iff the kind is one the ref store decides: relocated / name-only-refs /
unstarted / stillborn* / indeterminate.  It is NOT reached if the kind is `commits`,
`merged*` or `unverified`.

It also re-runs the pair discovery rather than trusting T451's hard-coded list, so a pair
that appeared after T451 measured is not invisible to it.

usage: 22-liveness.py <repo> <ready-tasks.py>
"""
import importlib.util
import json
import os
import re
import sys

REPO = os.path.abspath(sys.argv[1])
TOOL = os.path.abspath(sys.argv[2])
spec = importlib.util.spec_from_file_location("rt", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
if getattr(m, "branch_sweep", "x") is None:
    sys.exit("ABORT: branch_sweep not importable beside %s" % TOOL)
m.set_repo(REPO)

doc = json.load(open(os.path.join(REPO, ".softhouse", "tasks.json"), encoding="utf-8"))
tasks = {t["id"]: t for t in doc["tasks"]}
print("tool       : %s" % TOOL)
print("tasks.json : %d tasks" % len(tasks))
print("NOT_RUNNABLE (terminal statuses) : %s" % sorted(m.NOT_RUNNABLE))

# ---- discover the pairs FRESH, over every id in tasks.json ------------------------
ID = re.compile(r"(?<![0-9A-Za-z])((?:[Tt][0-9]+)|(?:A2-[0-9]+))(?![0-9A-Za-z])")
idx, note = m.ref_index()
if idx is None:
    sys.exit("ABORT: ref index unavailable (%s)" % note)
print("live refs  : %d" % len(idx.names()))

REF_ARM_KINDS = ("relocated", "name-only-refs", "unstarted", "stillborn",
                 "stillborn-carried", "indeterminate")
rows = []
for tid in sorted(tasks):
    t = tasks[tid]
    branch = t.get("branch") or ""
    refs, _n = m.refs_naming(tid, branch)
    carriers = []
    for ref in refs or []:
        ev = m.ref_content_evidence(tid, ref)
        ev0 = ev[0]
        if ev0:
            lead = ID.search(m.branch_sweep.short(ref).split("/")[-1])
            owner = lead.group(1).upper() if lead else "?"
            carriers.append((ref, owner, ev0[0][:100]))
    if not carriers:
        continue
    kind, _text = m.branch_wip(branch or None, tid)
    base = (kind or "").split("/")[0]
    action = m.reconcile_action(kind)
    pol = "REFUSE" if action.startswith("REFUSE") else "demote"
    reached = base in REF_ARM_KINDS
    terminal = t.get("status") in m.NOT_RUNNABLE
    rows.append((tid, t.get("status"), branch, kind, pol, reached, terminal, carriers))

print()
print("%-7s %-13s %-9s %-8s %-8s %s" % ("id", "status", "kind", "polarity",
                                        "ref arm", "carriers"))
print("-" * 118)
live_foreign = []
for tid, status, branch, kind, pol, reached, terminal, carriers in rows:
    foreign = [c for c in carriers if c[1] != tid]
    print("%-7s %-13s %-9s %-8s %-8s %s"
          % (tid, status, (kind or "")[:9], pol, "REACHED" if reached else "not",
             ", ".join("%s(%s)" % (m.branch_sweep.short(c[0]), c[1]) for c in carriers)))
    print("        recorded branch: %s" % (branch or "-"))
    if reached and not terminal and foreign and pol == "REFUSE":
        live_foreign.append((tid, status, kind, [c[0] for c in foreign]))
        print("        *** LIVE: a NON-TERMINAL id is REFUSED on FOREIGN work ***")

print()
print("=" * 118)
print("ids where a FOREIGN ref ACTUALLY buys a refusal today (arm reached, non-terminal,"
      " polarity REFUSE): %d" % len(live_foreign))
for x in live_foreign:
    print("   %s" % (x,))
if not live_foreign:
    print("   NONE on this tasks.json, on this day, with these refs. That is a statement")
    print("   about THIS measurement, not a property of the predicate: the same pairs")
    print("   become reachable the moment a recorded branch is pruned or parked.")
print()
print("Reachability is decided by the KIND `branch_wip` returns, not by status alone --")
print("which is the half T451's out/22-liveness.txt did not measure.")
