#!/usr/bin/env python3
"""T536 -- INCIDENT NUMBER THREE, which no blocklist has ever heard of.

T528's `probes/incident2.py` used `T540`. That id is now named in a review, in a handoff
and in this program's prose, so a fix that happened to special-case it would score green
against it. This probe therefore uses a task id that appears in NO blocklist, in no
review and in no baseline -- `T791` -- and asks the only question that matters:

    a brand-new task records a branch and a commit that never reached origin.
    Does ONE `--write-baseline` run make the guard green on it?

Under T527 the answer was yes: `INCIDENT_TASKS` / `INCIDENT_SHAS` are a blocklist of the
2026-09-04 incident, so anything else was waived, and the run printed
"REFUSED TO WAIVE 0 finding(s)" while doing it. Under T536 the baseline is frozen BY
GENERATION (`frozen_above`), so a claim from after the control existed is unwaivable
without a human raising the line in a committed file.

Cells:
  1. fresh incident, no baseline                 -> must REFUSE (exit 2)
  2. --write-baseline                            -> must REFUSE TO WAIVE it, by generation
  3. re-run                                      -> must STILL refuse (exit 2)
  4. the baseline file must not contain the id
  5. DELETE the baseline entirely, then --write-baseline again -- the freeze line must
     survive the file it was written in (it falls back to the module constant)
  6. lowercase `t508` -- the name lock-out must be case-folded (T528 F-3, second half)
  7. ANTI-VACUITY: a HISTORICAL finding (id below the line) must still be waivable, or
     this control has simply broken --write-baseline rather than frozen it.

Usage: python3 t536-incident3.py <repo-with-the-tools>
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
CB = os.path.join(REPO, ".softhouse", "bin", "check-branch-published.py")
TMP = tempfile.mkdtemp(prefix="t536-inc3-")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t536", GIT_AUTHOR_EMAIL="t536@x.invalid",
           GIT_COMMITTER_NAME="t536", GIT_COMMITTER_EMAIL="t536@x.invalid")
FAIL = 0


def g(cwd, *a):
    subprocess.run(("git",) + a, cwd=cwd, capture_output=True, env=ENV)


def fixture(d, tasks):
    """A repo whose ONLY defect is the tasks passed in: `softhouse/TP-pushed` is real and
    on origin, so a red verdict can only come from the injected claim."""
    w = os.path.join(d, "work")
    os.makedirs(os.path.join(w, ".softhouse", "bin"))
    g(w, "init", "--quiet", "-b", "main")
    shutil.copy(CB, os.path.join(w, ".softhouse", "bin"))
    subprocess.run(["git", "init", "--quiet", "--bare", "-b", "main",
                    os.path.join(d, "origin.git")], capture_output=True, env=ENV)
    g(w, "remote", "add", "origin", os.path.join(d, "origin.git"))
    open(os.path.join(w, "README"), "w").write("")
    g(w, "add", "-A")
    g(w, "commit", "--quiet", "-m", "root")
    g(w, "push", "--quiet", "-u", "origin", "main")
    g(w, "checkout", "--quiet", "-b", "softhouse/TP-pushed")
    open(os.path.join(w, "p.txt"), "w").write("p\n")
    g(w, "add", "-A")
    g(w, "commit", "--quiet", "-m", "TP work")
    g(w, "push", "--quiet", "origin", "softhouse/TP-pushed")
    g(w, "checkout", "--quiet", "main")
    open(os.path.join(w, ".softhouse", "tasks.json"), "w").write(
        json.dumps({"run_id": "t536-inc3", "tasks": tasks}))
    return w


def run(w, *extra):
    p = subprocess.run([sys.executable, os.path.join(w, ".softhouse", "bin",
                                                     "check-branch-published.py"),
                        "--repo", w] + list(extra),
                       capture_output=True, text=True, env=ENV, timeout=300)
    return p.returncode, p.stdout + p.stderr


def cell(name, ok, detail=""):
    global FAIL
    if not ok:
        FAIL += 1
    print("  %-52s %s %s" % (name, "PASS" if ok else "*** FAIL ***", detail))


BL = os.path.join(".softhouse", "capture", "t527-branch-published", "baseline.json")

# ---------------------------------------------------------------- the fresh incident
FRESH = [
    {"id": "TP", "status": "done", "branch": "softhouse/TP-pushed"},
    {"id": "T791", "status": "done", "branch": "softhouse/T791-lost-critical-path",
     "note": "landed c0ffee11 on softhouse/T791-lost-critical-path. THE CRITICAL PATH "
             "IS CLEARED."},
]

print("INCIDENT #3 -- a task id in no blocklist, no review and no baseline (T791)")
w = fixture(os.path.join(TMP, "fresh"), FRESH)
bl = os.path.join(w, BL)

rc, t = run(w)
named = [l.strip() for l in t.splitlines() if "UNBACKED" in l and l.startswith("  ")]
cell("1. fresh incident refused before any baseline", rc == 2, "exit %s %s" % (rc, named))

rc, t = run(w, "--write-baseline")
kept = [l.strip() for l in t.splitlines() if l.strip().startswith("KEEP")]
waived = [l.strip() for l in t.splitlines() if l.strip().startswith("WAIVE")]
freeze = [l.strip() for l in t.splitlines() if l.startswith("FREEZE LINE")]
print("     %s" % (freeze[0] if freeze else "(no freeze line printed!)"))
for k in kept:
    print("     %s" % k)
cell("2. --write-baseline REFUSES to waive it", not waived and len(kept) == 2,
     "waived=%d kept=%d" % (len(waived), len(kept)))

rc, t = run(w)
cell("3. re-run after the regeneration is STILL red", rc == 2, "exit %s" % rc)

keys = [e["key"] for e in json.load(open(bl))["waived"]]
cell("4. the baseline file contains no T791 key",
     not [k for k in keys if k.startswith("T791")], "%d key(s) total" % len(keys))

os.remove(bl)
rc, t = run(w, "--write-baseline")
waived = [l.strip() for l in t.splitlines() if l.strip().startswith("WAIVE")]
rc2, _ = run(w)
cell("5. deleting baseline.json does not lift the freeze line",
     not waived and rc2 == 2, "waived=%d, re-run exit %s" % (len(waived), rc2))

# ------------------------------------------------------- the case-folded name lock-out
w = fixture(os.path.join(TMP, "lower"), [
    {"id": "TP", "status": "done", "branch": "softhouse/TP-pushed"},
    {"id": "t508", "status": "done",
     "branch": "softhouse/T508-journalentry-insert-schema",
     "note": "landed 1abd3a11 on softhouse/T508-journalentry-insert-schema"}])
rc, t = run(w, "--write-baseline")
waived = [l.strip() for l in t.splitlines() if l.strip().startswith("WAIVE")]
kept = [l.strip() for l in t.splitlines() if l.strip().startswith("KEEP")]
for k in kept:
    print("     %s" % k)
cell("6. lowercase `t508` is KEPT, not WAIVED", not waived and len(kept) == 2,
     "waived=%d kept=%d" % (len(waived), len(kept)))

# ------------------------------------------------------------------- ANTI-VACUITY
# A control that refuses EVERYTHING is not a freeze, it is a break. A historical id must
# still be baselineable, or condition 3 has cost the tool its only pressure valve.
w = fixture(os.path.join(TMP, "hist"), [
    {"id": "TP", "status": "done", "branch": "softhouse/TP-pushed"},
    {"id": "T42", "status": "done", "branch": "softhouse/T42-ancient-history"}])
rc, t = run(w, "--write-baseline")
waived = [l.strip() for l in t.splitlines() if l.strip().startswith("WAIVE")]
rc2, _ = run(w)
cell("7. ANTI-VACUITY: a HISTORICAL id (T42) is still waivable",
     len(waived) == 1 and rc2 == 0, "waived=%d, re-run exit %s" % (len(waived), rc2))

print()
print("%d cell(s) failed." % FAIL)
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)
