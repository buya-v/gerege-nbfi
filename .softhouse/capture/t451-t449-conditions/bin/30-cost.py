#!/usr/bin/env python3
"""T451 -- C-T449-6.  Re-measure the ONE number the module states twice.

The shipped code comment says source 3 costs "0.070s for 9,730 paths ... versus 0.041s
for the handoff-only listing it widens -- net +0.029s once".  T350's handoff says
0.083 s.  Two spellings of one measurement is P-80's shape, so the number is re-taken
here and the code is made to carry the RANGE plus the command that reproduces it, not a
single host-specific decimal.

Cold, in-process, N runs each, median reported -- a single sample of a 70 ms git call on
a laptop is noise, and the defect being fixed is precisely that a noisy number was
written down twice as if it were exact.
"""
import importlib.util, os, statistics, subprocess, sys, time

REPO = os.path.abspath(".")
spec = importlib.util.spec_from_file_location(
    "rt", os.path.join(REPO, ".softhouse", "bin", "ready-tasks.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.set_repo(REPO)

N = 9


def bench(label, fn):
    xs = []
    for _ in range(N):
        t = time.monotonic()
        fn()
        xs.append(time.monotonic() - t)
    print("  %-46s median %.4fs  min %.4fs  max %.4fs"
          % (label, statistics.median(xs), min(xs), max(xs)))
    return statistics.median(xs)


def raw(*args):
    subprocess.run(["git", "-C", REPO] + list(args), capture_output=True)


print("N = %d runs each, median reported" % N)
full = bench("git ls-tree -r --name-only main  (source 3)",
             lambda: raw("ls-tree", "-r", "--name-only", "main"))
ho = bench("git ls-tree -r --name-only main -- .softhouse/handoff (source 2)",
           lambda: raw("ls-tree", "-r", "--name-only", "main", "--", ".softhouse/handoff"))
print("  %-46s %+.4fs" % ("NET ADDITIONAL cost of widening 2 -> 3", full - ho))

# main_tree() itself: the git call plus the lowercase-pair build, ONCE per process.
def mt():
    m._MAINTREE = ("uncached", None)
    m.main_tree()

mtc = bench("main_tree() in-process, cache cleared each run", mt)
entries, note = m.main_tree()
print("\n  paths tracked on main today: %d   (note: %s)" % (len(entries), note))

# per-task matching cost, which is the figure that actually scales
ids = ["T%d" % i for i in range(300, 300 + 60)]
t = time.monotonic()
for tid in ids:
    m.paths_naming(tid, entries)
per = (time.monotonic() - t) / len(ids)
print("  paths_naming() per task over %d paths: %.5fs" % (len(entries), per))
