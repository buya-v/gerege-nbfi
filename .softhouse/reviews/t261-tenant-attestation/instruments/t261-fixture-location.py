#!/usr/bin/env python3
"""T261 -- where did T250's DELIBERATELY-MALFORMED fixture actually end up?

T250 s.7 says an earlier BAR exited 2 because RED-DRIVE C shape 3 wrote a body
that is not JSON into a file named `NAME.req`, that the wire-float round-trip
guard REFUSED it, and that the fixture was RENAMED OUT of the graded population
rather than the guard being weakened.

This checks three separate things, because "it was renamed" is not the claim that
matters:
  1. WHICH files T250 adds that fall INSIDE the guard's derived population.
  2. Whether EVERY such file parses as JSON (i.e. nothing malformed is left where
     the grader can reach it).
  3. WHERE the malformed fixture is now, and whether the guard's OWN population
     function `derive()` reaches it.  The guard is imported and used verbatim, so
     this is the guard's answer, not mine.
"""
import json
import os
import sys

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, ".softhouse", "capture", "lib"))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "guard", os.path.join(ROOT, ".softhouse", "capture", "lib",
                          "check_wire_float_roundtrip.py"))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

files, rigs, reqdirs = guard.derive(ROOT)
print("guard population (its OWN derive()): %d files, %d rigs, %d req dirs"
      % (len(files), len(rigs), len(reqdirs)))
print("")

t250 = [f for f in files if "t250-tenant-attestation" in f]
print("T250 files INSIDE the guard's graded population : %d" % len(t250))
bad = []
for f in t250:
    rel = os.path.relpath(f, ROOT)
    try:
        with open(f, "rb") as fh:
            json.loads(fh.read().decode("utf-8"), parse_float=str)
        ok = "parses as JSON"
    except Exception as exc:
        ok = "*** DOES NOT PARSE: %s ***" % exc
        bad.append(rel)
    print("    %-88s %s" % (rel, ok))
print("")
if bad:
    print("MALFORMED FILES REACHABLE BY THE GRADER: %d" % len(bad))
    for b in bad:
        print("    %s" % b)
else:
    print("No malformed file inside the guard's population from T250.")
print("")

# where is the fixture now?
print("every T250-added file whose name mentions `req` or `inject`:")
capt = os.path.join(ROOT, ".softhouse", "capture", "t250-tenant-attestation")
for dp, dn, fn in os.walk(capt):
    for f in sorted(fn):
        p = os.path.join(dp, f)
        if "req" in f.lower() or "inject" in f.lower():
            inside = p in files
            print("    %-92s in-population=%s" % (os.path.relpath(p, ROOT), inside))
print("")
print("counter-check: rename the fixture BACK to *.req and ask derive() again --")
print("the guard must then reach it, or 'renamed out' would mean nothing.")
import shutil, tempfile
tmp = tempfile.mkdtemp()
probe_dir = os.path.join(ROOT, ".softhouse", "capture", "t250-tenant-attestation",
                         "evidence", "redC", "out")
src = os.path.join(probe_dir, "inject.req.NOT-JSON-BY-DESIGN.txt")
if os.path.isfile(src):
    dst = os.path.join(probe_dir, "T261PROBE.req")
    shutil.copy(src, dst)
    files2, _, _ = guard.derive(ROOT)
    reached = dst in files2
    print("    fixture copied to %s -> derive() reaches it: %s"
          % (os.path.relpath(dst, ROOT), reached))
    try:
        with open(dst, "rb") as fh:
            json.loads(fh.read().decode("utf-8"))
        print("    and it PARSES -- so it would not have tripped the guard (claim weakens)")
    except Exception as exc:
        print("    and it does NOT parse (%s) -- so under its old name it DID trip the guard"
              % type(exc).__name__)
    os.remove(dst)
    print("    probe removed; population back to %d" % len(guard.derive(ROOT)[0]))
else:
    print("    *** fixture NOT FOUND at %s ***" % os.path.relpath(src, ROOT))
