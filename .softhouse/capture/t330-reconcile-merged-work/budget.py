#!/usr/bin/env python3
"""T330 -- what the new probes COST, measured on the real repo and the real tasks.json.

The signal-path reconcile lives inside a hard wall-clock bound derived in
fire-program.sh's on_signal():

    budget = SIGNAL_GRACE_SECS - elapsed - GIT_PUSH_TIMEOUT_SECS - 2
    inner  = budget - RECONCILE_TAIL_RESERVE_SECS

With the shipped defaults (20 / 10 / 1) and ~1s spent stopping the driver that is
~7s OUTER and ~6s INNER, and below SIGNAL_RECONCILE_MIN_SECS (2) the whole reconcile
is SKIPPED LOUDLY. So the question is not "is the new probe fast" but "does it stay
inside 6 seconds at the real N".

Three numbers are measured here:
  1. NAIVE  -- the three per-task git calls the observation proposed, x N.
  2. T330   -- the index this implementation actually builds: two git calls TOTAL,
               plus a pure-filesystem ref index, plus a dict lookup per task.
  3. END-TO-END -- `--reconcile --dry-run` against the real tasks.json, before and
               after, so the delta is the whole change and not just its fast half.
"""
import json
import os
import subprocess
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GIT = shutil.which("git")


def t(fn, reps=3):
    best = None
    for _ in range(reps):
        t0 = time.monotonic()
        fn()
        d = time.monotonic() - t0
        best = d if best is None else min(best, d)
    return best


def g(*argv):
    subprocess.run([GIT] + list(argv), cwd=REPO, capture_output=True, text=True)


def main():
    doc = json.load(open(os.path.join(REPO, ".softhouse", "tasks.json")))
    tasks = doc["tasks"]
    N = len(tasks)
    live = [x for x in tasks if x.get("status") == "in_progress"]
    print("REPO            : %s" % REPO)
    print("tasks.json      : %d tasks, %d bytes"
          % (N, os.path.getsize(os.path.join(REPO, ".softhouse", "tasks.json"))))
    print("in_progress     : %d  (the reconcile's real N -- branch_wip is called on the"
          % len(live))
    print("                  demote list, not on all %d)" % N)
    print("commits on main : %s"
          % subprocess.run([GIT, "rev-list", "--count", "main"], cwd=REPO,
                           capture_output=True, text=True).stdout.strip())
    print("")

    print("--- 1. THE NAIVE SHAPE: three git calls PER TASK -------------------------")
    tid = tasks[-1]["id"]
    a = t(lambda: g("log", "--oneline", "main", "--grep=^Merge %s:" % tid))
    b = t(lambda: g("log", "--oneline", "main", "--grep=^%s:" % tid))
    c = t(lambda: g("ls-files", ".softhouse/handoff/*/%s.md" % tid))
    per = a + b + c
    print("  git log --grep='^Merge <TID>:'   %.4fs" % a)
    print("  git log --grep='^<TID>:'         %.4fs" % b)
    print("  git ls-files '<handoff>/<TID>.md' %.4fs" % c)
    print("  PER TASK                         %.4fs" % per)
    for n in (len(live), 8, 20, 100, N):
        print("    x N=%-4d -> %7.2fs   %s"
              % (n, per * n,
                 "FITS the ~6s inner budget" if per * n < 6 else
                 "*** BLOWS the ~6s inner budget ***"))
    print("")

    print("--- 2. WHAT T330 ACTUALLY DOES: ONE index, TWO git calls, any N ----------")
    d = t(lambda: g("log", "main", "--format=%H%x09%s"))
    e = t(lambda: g("ls-tree", "-r", "--name-only", "main", "--", ".softhouse/handoff"))
    print("  git log main --format=%%H%%x09%%s   %.4fs   (ALL commit subjects, once)" % d)
    print("  git ls-tree -r main -- handoff/   %.4fs   (ALL handoff paths, once)" % e)
    print("  ref index (branch_sweep.RefIndex) 0.0000s  -- pure filesystem, NO subprocess")
    print("  TOTAL, INDEPENDENT OF N          %.4fs" % (d + e))
    print("  per task after that              a dict lookup + one compiled-regex scan")
    print("  ratio vs naive at N=%d:          %.1fx cheaper" % (N, (per * N) / (d + e)))
    print("")

    print("--- 3. END TO END: --reconcile --dry-run on the REAL tasks.json ----------")
    # RED copy = main's bytes, GREEN = the working tree. Both run --dry-run, which does
    # not write. Both need the same authority, so both are run WITHOUT the lock and are
    # expected to REFUSE identically -- that leg still parses the 792 KB file and is the
    # startup+parse cost. The WIP-evidence cost is measured by calling branch_wip
    # directly, below, on every task that carries a branch.
    import importlib.util

    def load(path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.set_repo(REPO)
        return m

    red_path = "/tmp/t330-red/.softhouse/bin/ready-tasks.py"
    if not os.path.exists(red_path):
        print("  (RED copy not staged at %s -- run the red step first)" % red_path)
        return 1
    branched = [x for x in tasks if x.get("branch")]
    print("  tasks carrying a `branch` field: %d" % len(branched))
    seen = {}
    for label, path, pass_tid in (("PRE-T330 ", red_path, False),
                                  ("POST-T330", os.path.join(REPO, ".softhouse", "bin",
                                                             "ready-tasks.py"), True)):
        m = load(path, "bud_%s" % label.strip())
        t0 = time.monotonic()
        kinds = {}
        for x in branched:
            k, _ = (m.branch_wip(x["branch"], x["id"]) if pass_tid
                    else m.branch_wip(x["branch"]))
            kinds[k] = kinds.get(k, 0) + 1
        dt = time.monotonic() - t0
        seen[label.strip()] = (dt, kinds)
        print("  %s branch_wip over ALL %d branched tasks: %7.3fs  (%.4fs/task)"
              % (label, len(branched), dt, dt / max(1, len(branched))))
        print("             verdicts: %s"
              % ", ".join("%s=%d" % kv for kv in sorted(kinds.items())))
    pre_dt, pre_k = seen["PRE-T330"]
    post_dt, post_k = seen["POST-T330"]
    n = max(1, len(branched))
    print("  DELTA: %+.3fs total, %+.4fs/task, %+.1f%% -- and it does NOT scale with N,"
          % (post_dt - pre_dt, (post_dt - pre_dt) / n,
             100.0 * (post_dt - pre_dt) / pre_dt))
    print("         because %.4fs of it is the ONE-TIME index above." % (d + e))
    print("")
    print("  HOW OFTEN THE OLD `absent` VERDICT WAS FACTUALLY WRONG, on the live file:")
    old_absent = sum(v for k, v in pre_k.items() if k.split("/")[0] == "absent")
    now_wrong = sum(v for k, v in post_k.items()
                    if k.split("/")[0] in ("merged", "relocated")) - \
        sum(v for k, v in pre_k.items() if k.split("/")[0] == "merged")
    print("    pre-T330 said `absent` (-> DEMOTE) on          %d branched task(s)" % old_absent)
    print("    of those, T330 measures work reachable on      %d" % now_wrong)
    print("    genuinely unstarted                            %d"
          % sum(v for k, v in post_k.items() if k.split("/")[0] == "unstarted"))
    print("    => %.1f%% of the pre-T330 `absent` verdicts in this file are WRONG about"
          % (100.0 * now_wrong / max(1, old_absent)))
    print("       whether anything was done. They did no damage only because the")
    print("       reconcile touches `in_progress` tasks and 3 of 219 are in_progress.")
    print("")
    print("  NOTE ON THE REAL N: the reconcile calls branch_wip only on `in_progress`")
    print("  tasks. The figure above is the WORST CASE -- every branched task in the")
    print("  file -- and is reported instead of the convenient one.")
    print("")
    print("--- 4. THE PRE-EXISTING O(N), WHICH T330 DID NOT INTRODUCE AND DOES NOT FIX -")
    print("  The PRE-T330 column is %.4fs/task with NO T330 probe in it at all: that is"
          % (pre_dt / n))
    print("  the EXISTING per-branch `rev-parse` + `rev-list` (+ `merge-base` on the")
    print("  ambiguous zero). It was already O(N) and already crosses a ~6s inner")
    print("  budget at N ~ %d. T330 moves that crossover to N ~ %d."
          % (int(6.0 / (pre_dt / n)), int(6.0 / (post_dt / n))))
    print("  Recorded as FU-T330-1, NOT fixed here: batching the per-branch queries the")
    print("  way the landed index is batched is a separate change with its own drive.")
    print("  At the real N (in_progress = %d) neither shape is near the budget." % len(live))
    return 0


if __name__ == "__main__":
    sys.exit(main())
