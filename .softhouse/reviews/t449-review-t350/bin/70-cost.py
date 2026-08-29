#!/usr/bin/env python3
"""T449 -- independent cost measurement of T350's additions."""
import importlib.util, subprocess, sys, time

REPO = sys.argv[1]
spec = importlib.util.spec_from_file_location("rt", "/tmp/t449/mods/rt_t350.py")
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
T.set_repo(REPO)

t0 = time.monotonic(); T.landed_index(); t1 = time.monotonic()
T.main_tree(); t2 = time.monotonic()
entries, note = T.main_tree()
print("landed_index()  (commit subjects + handoff listing) : %.4f s" % (t1 - t0))
print("main_tree()     NEW, one `git ls-tree -r main`      : %.4f s" % (t2 - t1))
print("main_tree note: %s" % note)
print("paths listed: %d" % len(entries))

# the handoff-only listing main_tree() widens, timed the same way
t3 = time.monotonic()
subprocess.run(["git", "ls-tree", "-r", "--name-only", "main", "--", ".softhouse/handoff"],
               cwd=REPO, capture_output=True, text=True)
t4 = time.monotonic()
t5 = time.monotonic()
subprocess.run(["git", "ls-tree", "-r", "--name-only", "main"], cwd=REPO,
               capture_output=True, text=True)
t6 = time.monotonic()
print("\nraw `git ls-tree -r main -- .softhouse/handoff` : %.4f s" % (t4 - t3))
print("raw `git ls-tree -r main`                      : %.4f s" % (t6 - t5))
print("net additional cost, once per process          : %.4f s" % ((t6 - t5) - (t4 - t3)))

ids = ["T%d" % n for n in range(100, 460)]
t7 = time.monotonic()
for tid in ids:
    T.landed_evidence(tid)
t8 = time.monotonic()
print("\nlanded_evidence() over %d ids: %.4f s total, %.5f s/task"
      % (len(ids), t8 - t7, (t8 - t7) / len(ids)))

# ref probe cost, on a ref that exists
t9 = time.monotonic()
T.ref_content_evidence("T350", "softhouse/T350-reconcile-content")
t10 = time.monotonic()
print("ref_content_evidence() for ONE ref (2 git calls): %.4f s" % (t10 - t9))
print("MAX_REFS_PROBED = %d" % T.MAX_REFS_PROBED)

# the READY listing's total added cost, 53 non-terminal tasks
t11 = time.monotonic()
for tid in ids[:54]:
    T.landed_evidence(tid)
t12 = time.monotonic()
print("54 non-terminal tasks through the READY flag    : %.4f s" % (t12 - t11))
