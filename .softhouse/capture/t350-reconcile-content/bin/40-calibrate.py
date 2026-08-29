#!/usr/bin/env python3
"""T350 -- CALIBRATION. How often does the new `stillborn` verdict fire, and could it
demote work that really landed?

`stillborn` is the ONE arm where T350 moves a verdict from REFUSE to DEMOTE on a branch
that git says is an ancestor of main. That is the destructive direction, so the rate is
measured rather than argued.

Method: every local head in this checkout that (a) has ZERO commits ahead of main and
(b) IS an ancestor of main -- i.e. every branch the pre-T350 code would have called
`merged`. For each, ask the T350 question: is anything OWNING that branch's task id on
main? Prints the split, and lists every branch that flips REFUSE -> DEMOTE so the flip
set can be inspected by hand rather than trusted as a count (P-80).

Also times `landed_evidence` per task, because it now runs for every non-terminal task
in the READY/BLOCKED listing rather than only for `in_progress` ones.
"""
import importlib.util
import os
import re
import subprocess
import sys
import time

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
MOD = os.path.join(REPO, ".softhouse", "bin", "ready-tasks.py")

spec = importlib.util.spec_from_file_location("rt", MOD)
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
rt.set_repo(REPO)


def git(*a):
    return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True,
                          text=True).stdout.strip()


heads = git("for-each-ref", "--format=%(refname:short)", "refs/heads").splitlines()
print("repo:  %s" % REPO)
print("module: %s" % MOD)
print("local heads: %d" % len(heads))
print()

# ---- warm the two indexes ONCE, and time them ------------------------------------
t0 = time.monotonic()
rt.landed_index()
t1 = time.monotonic()
rt.main_tree()
t2 = time.monotonic()
print("index build (once per process, independent of task count):")
print("  landed_index()  commit subjects + exact handoff names : %.4fs" % (t1 - t0))
print("  main_tree()     every tracked path on main            : %.4fs" % (t2 - t1))
entries, note = rt.main_tree()
print("  main_tree note: %s" % note)
print()

# ---- per-task cost ----------------------------------------------------------------
ids = ["T%d" % n for n in range(100, 460)]
t0 = time.monotonic()
for tid in ids:
    rt.landed_evidence(tid)
dt = time.monotonic() - t0
print("landed_evidence() over %d ids: %.4fs total, %.5fs per task"
      % (len(ids), dt, dt / len(ids)))
print()

# ---- the stillborn calibration -----------------------------------------------------
print("=" * 78)
print("BRANCHES THE PRE-T350 CODE CALLED `merged` (0 ahead of main AND ancestor of main)")
print("=" * 78)
merged_kept, flipped, no_id = [], [], []
for h in heads:
    n = git("rev-list", "--count", "main.." + h)
    if n != "0":
        continue
    rc = subprocess.run(["git", "-C", REPO, "merge-base", "--is-ancestor", h, "main"],
                        capture_output=True).returncode
    if rc != 0:
        continue
    m = re.search(r"(?<![0-9A-Za-z])([A-Za-z]+-?T?\d+(?:-\d+)?)(?![0-9A-Za-z])",
                  h.split("/")[-1])
    if not m:
        no_id.append(h)
        continue
    tid = m.group(1)
    ev, complete, _ = rt.landed_evidence(tid)
    if ev:
        merged_kept.append((h, tid, ev[0][:70]))
    elif not complete:
        merged_kept.append((h, tid, "PROBE DID NOT RUN -> merged-unverified, still REFUSES"))
    else:
        flipped.append((h, tid))
print("  still `merged` (REFUSE), corroborated by content on main : %d" % len(merged_kept))
print("  flip to `stillborn` (DEMOTE), nothing owning on main     : %d" % len(flipped))
print("  no task id parseable from the branch name                : %d" % len(no_id))
print()
print("EVERY FLIP, LISTED -- inspect these, do not trust the count:")
for h, tid in flipped:
    head = git("log", "-1", "--format=%h %s", h)
    print("  %-56s id=%-9s head: %s" % (h, tid, head[:90]))
if not flipped:
    print("  (none)")
print()
print("A SAMPLE OF THE ONES THAT STAY `merged`:")
for h, tid, why in merged_kept[:10]:
    print("  %-56s id=%-9s %s" % (h, tid, why))
print("  ... %d total" % len(merged_kept))
