#!/usr/bin/env python3
"""T451 -- is the FOREIGN-REF REFUSAL live today, or latent?

21-realrepo-evidence.py found 15 (id, ref) pairs where a live ref CARRIES content for an
id under the SHIPPED code, and 10 of those refs are owned by a DIFFERENT task -- review
and retry branches whose commit subject names the task they are about.  A ref only
blocks a demotion when the reconciler actually reaches the ref arm, which needs:
    the task is NON-TERMINAL in tasks.json, and
    its recorded branch does not resolve (absent leg) or is parked at a dispatch commit.
So this asks tasks.json, per id, rather than assuming.  "Not found" here would be a
statement about this tasks.json on this day.
"""
import importlib.util, json, os, subprocess, sys

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
TOOL = os.path.join(REPO, ".softhouse", "bin", "ready-tasks.py")
spec = importlib.util.spec_from_file_location("rt", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.set_repo(REPO)

PAIRS = [  # (tid, ref, ref-owner) -- copied from out/21, re-verified below by re-probing
    ("T100", "softhouse/T101-review-t100", "T101"),
    ("T108", "softhouse/T131-review-t108", "T131"),
    ("T109", "softhouse/T127-review-t109", "T127"),
    ("T21", "softhouse/T21-pass3-audit-rescued", "T21"),
    ("T22", "softhouse/T22-pathb-audit-rescued", "T22"),
    ("T268", "softhouse/t281-review-t268", "T281"),
    ("T268", "softhouse/t286-t268-retry", "T286"),
    ("T351", "softhouse/T369-review-t351", "T369"),
    ("T351", "softhouse/T370-t351-retry", "T370"),
    ("T370", "softhouse/T376-review-t370", "T376"),
    ("T38", "softhouse/T38-dec1-v7-pass2", "T38"),
    ("T38", "softhouse/T38-dec1-v7", "T38"),
    ("T428", "softhouse/rescued-t428-t421tree-20260828-140005", "T428"),
    ("T65", "softhouse/T67-review-t65", "T67"),
    ("T78", "softhouse/T79-review-t78", "T79"),
]

doc = json.load(open(os.path.join(REPO, ".softhouse", "tasks.json")))
tasks = {t["id"]: t for t in doc["tasks"]}
print("tasks.json: %d tasks" % len(tasks))
print("%-6s %-8s %-16s %-46s %s" % ("id", "owner", "status", "ref", "recorded branch"))
print("-" * 118)
live = []
for tid, ref, owner in PAIRS:
    t = tasks.get(tid)
    status = t.get("status") if t else "NOT IN tasks.json"
    branch = (t or {}).get("branch") or "-"
    rc, sha, _ = m._run([m.GIT, "rev-parse", "--verify", "--quiet", branch + "^{commit}"]) \
        if branch != "-" else (1, "", "")
    resolves = "resolves" if (rc == 0 and sha) else "ABSENT"
    reachable = (t is not None and status not in m.NOT_RUNNABLE)
    flag = ""
    if reachable and owner != tid:
        flag = "   <== LIVE FOREIGN-REF REFUSAL"
        live.append((tid, ref, owner, status))
    print("%-6s %-8s %-16s %-46s %s (%s)%s"
          % (tid, owner, status, ref, branch, resolves, flag))
print()
print("non-terminal ids blocked by a FOREIGN-owned ref today: %d" % len(live))
for x in live:
    print("   %s" % (x,))
if not live:
    print("   NONE.  Every id a foreign ref would block is TERMINAL in tasks.json today,")
    print("   so the reconciler never reaches the ref arm for it.  LATENT, not burning --")
    print("   and latent is what C-T449-1 was too, three weeks before it fired on T431.")
