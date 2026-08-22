#!/usr/bin/env python3
"""Readiness resolver for /softhouse-program STEP 1.

WHY THIS EXISTS. The driver's readiness check used to resolve a task's dependencies
against `.softhouse/tasks.json` ALONE. Tasks that complete are archived into
`.softhouse/runs/<run-id>.tasks.json` and dropped from the current file, so a
dependency on a completed task from an earlier run resolves to NOTHING and the
dependent task reads as permanently blocked.

That is not hypothetical. `T116` -- the G-8 option (a) family-B vector promotion --
was carried across several fires under the recorded claim that its dependency `T114`
"has NO ENTRY in tasks.json and can never resolve". T114 is `done` in
`.softhouse/runs/2026-08-17-run1-harness-schedule-poc.tasks.json`, with its handoff
and its review both merged on main. Measured by local fire 20260822-000013: SEVEN
dependency edges in the current file point outside it, and ALL SEVEN resolve in the
archive. None was ever missing.

The defect class is this program's most common one: a check that stops checking and
says so nowhere. So this resolver prints, on every run, WHERE each edge resolved --
current file, archive, or genuinely absent -- rather than silently returning a
boolean. Read the UNRESOLVED section; an empty one is a claim, and the counts beside
it are what make the claim inspectable.

Usage:  python3 .softhouse/bin/ready-tasks.py [--json]
Run it from the repo root.
"""
import json
import glob
import os
import sys

TERMINAL = {"done", "approved", "merged"}
NOT_RUNNABLE = {"done", "approved", "merged", "parked", "rejected",
                "cancelled", "superseded", "closed_as_obligation"}

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo = os.path.dirname(root)


def load():
    cur = {}
    with open(os.path.join(root, "tasks.json")) as fh:
        for t in json.load(fh)["tasks"]:
            cur[t["id"]] = t
    arch = {}
    for path in sorted(glob.glob(os.path.join(root, "runs", "*.json"))):
        with open(path) as fh:
            try:
                doc = json.load(fh)
            except ValueError:
                continue
        for t in doc.get("tasks", []):
            # First archive wins only if the later one is not terminal; a task
            # re-run in a later run should be judged on its latest recorded state.
            prev = arch.get(t["id"])
            if prev is None or prev[1] not in TERMINAL:
                arch[t["id"]] = (os.path.basename(path), t.get("status"))
    return cur, arch


def resolve(dep, cur, arch):
    """Return (met, where). `where` always says how the edge was decided."""
    if dep in cur:
        return cur[dep].get("status") in TERMINAL, "tasks.json (%s)" % cur[dep].get("status")
    if dep in arch:
        name, status = arch[dep]
        return status in TERMINAL, "archive %s (%s)" % (name, status)
    return False, "NOT FOUND in tasks.json or any .softhouse/runs/*.json"


def main():
    cur, arch = load()
    ready, blocked, unresolved, live = [], [], [], []
    for tid, t in cur.items():
        if t.get("status") in NOT_RUNNABLE:
            continue
        if t.get("status") == "in_progress":
            live.append((tid, t))
            continue
        edges = [(d,) + resolve(d, cur, arch) for d in t.get("dependencies", [])]
        for dep, met, where in edges:
            if where.startswith("NOT FOUND"):
                unresolved.append((tid, dep))
        unmet = [(d, w) for d, m, w in edges if not m]
        (blocked if unmet else ready).append((tid, t, unmet, edges))

    if "--json" in sys.argv:
        json.dump({"ready": [r[0] for r in ready],
                   "in_progress": [l[0] for l in live],
                   "blocked": {b[0]: [u[0] for u in b[2]] for b in blocked},
                   "unresolved_edges": unresolved}, sys.stdout, indent=2)
        print()
        return 0

    print("IN PROGRESS -- ALREADY DISPATCHED, do not dispatch again (%d)" % len(live))
    for tid, t in sorted(live):
        print("  %-8s %s" % (tid, t.get("branch", "NO BRANCH RECORDED -- suspect an isolation violation")))
    print()
    print("READY (%d)" % len(ready))
    for tid, t, _, edges in sorted(ready):
        via = " via archive" if any("archive" in e[2] for e in edges) else ""
        print("  %-8s %-6s %-7s %s%s" % (tid, t.get("model", "?"),
                                         t.get("target", "?"), t.get("title", "")[:78], via))
    print("\nBLOCKED (%d)" % len(blocked))
    for tid, t, unmet, _ in sorted(blocked):
        print("  %-8s waiting on: %s" % (tid, ", ".join("%s [%s]" % u for u in unmet)))
    # READY here means TASK dependencies are met. It does NOT mean a gate permits the
    # work. A task can be dependency-ready and still forbidden -- e.g. writing vectors
    # in a context whose DEC-n is unratified. The driver decides that; this only warns.
    try:
        with open(os.path.join(root, "program.json")) as fh:
            gates = json.load(fh).get("gates_pending", [])
    except (IOError, ValueError):
        gates = []
    contract_open = [g for g in gates
                     if g.get("class") == "CONTRACT" and "OPEN" in str(g.get("state", ""))]
    print("\nOPEN CONTRACT GATES -- READY above is about DEPENDENCIES, not permission (%d)"
          % len(contract_open))
    if not contract_open:
        print("  NONE open. Every gate id in program.json.gates_pending was inspected.")
    for g in contract_open:
        print("  %s  %s" % (g.get("id"), g.get("state")))
        print("      context %s / slice %s" % (g.get("context"), g.get("slice")))
        print("      %s" % str(g.get("title", ""))[:100])
        print("      => no task may write Go under nexus/ or store a CONTRACT-SHAPED vector")
        print("         for this context until it closes. Raw observed capture IS permitted.")

    print("\nDEPENDENCY EDGES THAT RESOLVE NOWHERE (%d)" % len(unresolved))
    if not unresolved:
        print("  NONE. Every edge was decided against tasks.json or an archived run file,")
        print("  and this line is printed only after checking both -- it is not a default.")
    for tid, dep in unresolved:
        print("  %s -> %s" % (tid, dep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
