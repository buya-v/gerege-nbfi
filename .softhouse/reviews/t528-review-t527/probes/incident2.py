#!/usr/bin/env python3
"""T528 -- INCIDENT NUMBER TWO.

T527 states its own residual risk: a later `--write-baseline` could launder a fresh
incident, and two things stand against it -- a hardcoded lock-out list and the fact
that the regeneration prints what it adds.

This measures whether the lock-out list actually protects anything other than the
2026-09-04 incident. A NEW task, T540, records a branch and a commit that never
reached origin. That is incident #2, in the same shape."""
import os, subprocess, sys, tempfile, shutil, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import mkclean, ENV, TMP

REPO = sys.argv[1]
CB = "check-branch-published.py"

w = mkclean(os.path.join(TMP, "inc2"))
bl = os.path.join(w, ".softhouse", "capture", "t527-branch-published", "baseline.json")

# incident #2: a NEW task claiming a branch and a commit origin never heard of
open(os.path.join(w, ".softhouse", "tasks.json"), "w").write(json.dumps({
    "run_id": "x",
    "tasks": [
        {"id": "TP", "status": "done", "branch": "softhouse/TP-pushed"},
        {"id": "T540", "status": "done", "branch": "softhouse/T540-critical-path",
         "note": "landed deadbe1f on softhouse/T540-critical-path. THE CRITICAL PATH "
                 "IS CLEARED."},
    ]}))


def run(*extra):
    p = subprocess.run([sys.executable, os.path.join(w, ".softhouse", "bin", CB),
                        "--repo", w] + list(extra), capture_output=True, text=True,
                       env=ENV, timeout=300)
    return p.returncode, p.stdout + p.stderr


rc, t = run()
print("1. before any baseline           -> exit %s" % rc)
for l in t.splitlines():
    if "UNBACKED" in l and "  " == l[:2]:
        print("     " + l.strip())

rc, t = run("--write-baseline")
print("\n2. `--write-baseline` (what an agent staring at a red guard would reach for)")
print("   exit %s" % rc)
for l in t.splitlines():
    if l.startswith("wrote") or l.strip().startswith("WAIVE") \
            or l.startswith("REFUSED") or l.strip().startswith("KEEP"):
        print("     " + l.strip())

rc, t = run()
print("\n3. re-run after the regeneration -> exit %s" % rc)
print("     %s" % [l for l in t.splitlines() if "check-branch-published:" in l])
print("\n   INCIDENT #2 IS NOW %s" % ("LAUNDERED -- the guard is green on lost work"
                                      if rc == 0 else "still refused"))

print("\n4. does the lock-out list protect T540? entries now in the baseline:")
d = json.load(open(bl))
for e in d["waived"]:
    print("     %-6s %-34s %s" % (e["task"], e["subject"], e["kind"]))
print("   refuses_to_waive =", d["refuses_to_waive"])

print("\n5. case sensitivity of the lock-out: a record spelling the id 't508'")
open(os.path.join(w, ".softhouse", "tasks.json"), "w").write(json.dumps({
    "run_id": "x", "tasks": [
        {"id": "t508", "status": "done",
         "branch": "softhouse/T508-journalentry-insert-schema",
         "note": "landed 1abd3a11 on softhouse/T508-journalentry-insert-schema"}]}))
os.remove(bl)
rc, t = run("--write-baseline")
kept = [l.strip() for l in t.splitlines() if l.strip().startswith("KEEP")]
waived = [l.strip() for l in t.splitlines() if l.strip().startswith("WAIVE")]
print("     WAIVED:", waived)
print("     KEPT  :", kept)
shutil.rmtree(TMP, ignore_errors=True)
