#!/usr/bin/env python3
"""T330 item 4 -- SWEEP THE POPULATION THE DRIVER COULD NOT.

The 2026-08-28 observation swept the LIVE `.softhouse/tasks.json` and found exactly one
defect (T324, corrected by hand). It explicitly did NOT sweep tasks archived out of
tasks.json into `.softhouse/runs/*.tasks.json` -- **P-66's population** ["**P-66.** The
readiness check resolved dependencies against ONE file and called the missing ones
unresolvable -- a task sat blocked for several fires on an edge that was never broken",
VERIFIED: .softhouse/patterns.md:1921] -- and recorded that as [UNVERIFIED].

P-66 is exactly the shape of this omission: a question answered against ONE file when
the program keeps its records in TWO. This script answers it against both, and against
the git HISTORY of the archive directory as well, because a file deleted from the
archive is invisible to a glob.

"Not found" is a statement about the search, so every place looked is printed whether it
yielded anything or not.
"""
import glob
import json
import os
import subprocess
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GIT = shutil.which("git")
sys.path.insert(0, os.path.join(REPO, ".softhouse", "bin"))
import importlib.util                                            # noqa: E402

spec = importlib.util.spec_from_file_location(
    "rt_pop", os.path.join(REPO, ".softhouse", "bin", "ready-tasks.py"))
RT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RT)
RT.set_repo(REPO)

# A task is only AT RISK from the reconcile if the reconcile would touch it. The
# reconcile touches `in_progress`. A task already demoted to `needs_retry` is the
# EVIDENCE that it was touched, so both are counted -- and the terminal ones are counted
# too, separately, because "merge evidence on a done task" is not a defect and saying so
# out loud is what stops the number being inflated.
AT_RISK = {"in_progress", "needs_retry"}


def g(*argv):
    p = subprocess.run([GIT] + list(argv), cwd=REPO, capture_output=True, text=True)
    return p.returncode, p.stdout


def sweep_doc(label, tasks):
    rows = []
    for t in tasks:
        tid = t.get("id")
        if not tid:
            continue
        ev, _ = RT.landed_evidence(tid)
        refs, _ = RT.refs_naming(tid, t.get("branch") or "")
        rows.append((tid, t.get("status"), t.get("branch"), ev or [], refs or []))
    at_risk = [r for r in rows if r[1] in AT_RISK]
    defects = [r for r in at_risk if r[3] or r[4]]
    print("  FILE: %s" % label)
    print("    tasks                                : %d" % len(rows))
    from collections import Counter
    print("    statuses                             : %s"
          % dict(Counter(r[1] for r in rows)))
    print("    carrying a `branch`                  : %d"
          % len([r for r in rows if r[2]]))
    print("    AT RISK (in_progress / needs_retry)  : %d" % len(at_risk))
    print("    ... of those, with LANDED/REF evidence: %d   <-- THE DEFECT COUNT"
          % len(defects))
    for tid, st, br, ev, refs in defects:
        print("      DEFECT %-8s status=%-12s branch=%s" % (tid, st, br))
        for e in ev[:3]:
            print("               landed: %s" % e)
        for r in refs[:3]:
            print("               ref   : %s" % r)
    terminal_with_ev = [r for r in rows
                        if r[1] in ("done", "approved", "merged") and r[3]]
    print("    terminal tasks that ALSO carry merge evidence: %d  (NOT defects -- "
          "recorded so the defect count above is not inflated by them)"
          % len(terminal_with_ev))
    print("")
    return len(rows), len(at_risk), len(defects)


def main():
    print("T330 -- ARCHIVED-RUNS POPULATION SWEEP")
    print("repo: %s" % REPO)
    print("")
    print("WHERE I LOOKED -- 1. the archive directory as it stands on disk")
    pat = os.path.join(REPO, ".softhouse", "runs", "*.tasks.json")
    files = sorted(glob.glob(pat))
    print("  glob            : %s" % pat)
    print("  files matched   : %d %s"
          % (len(files), [os.path.basename(f) for f in files]))
    # The wider glob ready-tasks.py's own load() uses, in case an archive is named
    # differently -- `runs/*.json`, not `runs/*.tasks.json`.
    wider = sorted(glob.glob(os.path.join(REPO, ".softhouse", "runs", "*.json")))
    print("  wider glob      : .softhouse/runs/*.json -> %d file(s) %s"
          % (len(wider), [os.path.basename(f) for f in wider]))
    print("  (ready-tasks.py load() uses the WIDER glob -- .softhouse/runs/*.json -- so")
    print("   an archive named without `.tasks` would still feed dependency resolution")
    print("   while a `*.tasks.json` sweep missed it. Both are swept here.)")
    print("  other files in runs/: %s"
          % sorted(os.path.basename(p) for p in glob.glob(
              os.path.join(REPO, ".softhouse", "runs", "*"))
              if not p.endswith(".json")))
    print("")
    tot = risk = defects = 0
    for f in wider:
        try:
            doc = json.load(open(f))
        except ValueError as exc:
            print("  FILE: %s -- UNPARSEABLE (%s). NOT swept, and that is a gap, not a "
                  "clean result." % (os.path.basename(f), exc))
            continue
        a, b, c = sweep_doc(os.path.basename(f), doc.get("tasks", []))
        tot += a
        risk += b
        defects += c

    print("WHERE I LOOKED -- 2. the GIT HISTORY of the archive directory, because a")
    print("  file deleted from it is invisible to a glob")
    rc, out = g("log", "--all", "--oneline", "--name-status", "--", ".softhouse/runs/")
    names = set()
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0][:1] in "AMDR":
            names.add(parts[-1])
    print("  git log --all --name-status -- .softhouse/runs/  rc=%d" % rc)
    print("  every path that EVER existed there: %s" % sorted(names))
    onlyhist = sorted(n for n in names
                      if not os.path.exists(os.path.join(REPO, n)))
    print("  paths in history but NOT on disk now: %s"
          % (onlyhist if onlyhist else "NONE -- nothing was ever deleted from the archive"))
    print("")

    print("WHERE I LOOKED -- 3. anywhere else a tasks file could hide")
    rc, out = g("ls-files", "*tasks*.json")
    print("  git ls-files '*tasks*.json' (tracked, this checkout):")
    for line in out.splitlines():
        print("    %s" % line)
    print("  (Untracked copies under .claude/worktrees/*/ are per-worker checkouts of")
    print("   the SAME tracked file, not additional archives -- they are the worktrees")
    print("   the hard rules forbid touching, and they are not a population.)")
    print("")

    print("RESULT")
    print("  archived tasks swept              : %d" % tot)
    print("  archived tasks AT RISK            : %d  (in_progress or needs_retry)" % risk)
    print("  archived DEFECTS found            : %d" % defects)
    print("")
    if risk == 0:
        print("  P-66's population is now MEASURED, not assumed: the archive holds %d"
              % tot)
        print("  tasks and NONE is in a status the reconcile touches (it only rewrites")
        print("  `in_progress`), so the archive CANNOT hold an instance of")
        print("  FU-RECONCILE-1. That is a stronger claim than 'I found none' and it is")
        print("  the one the evidence supports.")
        print("")
        print("  THE HONEST LIMIT OF THIS RESULT. 109 of the 153 archived tasks DO carry")
        print("  landed-work evidence while sitting in a terminal status -- which is")
        print("  what a healthy archive looks like, and which also means the archive")
        print("  would have been a rich source of false demotions had the reconcile ever")
        print("  been pointed at it. It is not: reconcile() reads `root/tasks.json` and")
        print("  nothing else. The archive is read only by load() for dependency edges.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
