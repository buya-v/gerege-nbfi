#!/usr/bin/env python3
"""Re-run of the two cells whose first form was a test-design error, plus the
exit-code detail for the malformed-record cell."""
import os, subprocess, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import mkclean, ENV, TMP

REPO = sys.argv[1]


def run(w, extra=(), env=None):
    p = subprocess.run([sys.executable,
                        os.path.join(w, ".softhouse", "bin", "ready-tasks.py"),
                        "--repo", w] + list(extra),
                       capture_output=True, text=True, timeout=400, env=env or ENV)
    return p.returncode, p.stdout + p.stderr


print("F2. archive that is unparseable JSON (root defeats chmod 000)")
w = mkclean(os.path.join(TMP, "f2"))
os.makedirs(os.path.join(w, ".softhouse", "runs"))
open(os.path.join(w, ".softhouse", "runs", "old.tasks.json"), "w").write("{broken")
rc, t = run(w)
print("   ready-tasks.py exit %s ; checker said: %s" % (
    rc, [l for l in t.splitlines() if "reason:" in l or "CLEAN" in l][:2]))

print("\nF3. archive whose top level has no tasks list")
w = mkclean(os.path.join(TMP, "f3"))
os.makedirs(os.path.join(w, ".softhouse", "runs"))
open(os.path.join(w, ".softhouse", "runs", "old.tasks.json"), "w").write('{"x":1}')
rc, t = run(w)
print("   ready-tasks.py exit %s ; %s" % (
    rc, [l for l in t.splitlines() if "reason:" in l or "CLEAN" in l][:2]))

print("\nH2. checker raises INSIDE check() -- injected before the return")
w = mkclean(os.path.join(TMP, "h2"))
p = os.path.join(w, ".softhouse", "bin", "check-branch-published.py")
src = open(p).read()
needle = "    baseline = load_baseline(baseline_path)"
assert needle in src, "anchor not found"
open(p, "w").write(src.replace(needle,
                               needle + '\n    raise RuntimeError("injected mid-run")'))
rc, t = run(w)
print("   ready-tasks.py exit %s" % rc)
for ln in t.splitlines():
    if ">>>" in ln or "Traceback" in ln or "RuntimeError" in ln or "CLEAN" in ln:
        print("     " + ln)

print("\nI2. checker replaced by a stub that exits 0 silently")
w = mkclean(os.path.join(TMP, "i2"))
open(os.path.join(w, ".softhouse", "bin", "check-branch-published.py"), "w").write(
    "import sys\nsys.exit(0)\n")
open(os.path.join(w, ".softhouse", "tasks.json"), "w").write(
    '{"run_id":"x","tasks":[{"id":"TN","status":"done",'
    '"branch":"softhouse/TN-never-pushed"}]}')
rc, t = run(w)
print("   record is DIRTY (TN never pushed) but checker is a silent stub ->"
      " ready-tasks.py exit %s" % rc)
print("   gate printed:", [l for l in t.splitlines()
                           if "STEP 0" in l or "NOT CLEAN" in l][:3])
shutil.rmtree(TMP, ignore_errors=True)
