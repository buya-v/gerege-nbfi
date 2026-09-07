#!/usr/bin/env python3
"""T537 item 3 -- THE BASELINE FREEZE, driven with ids nothing has ever seen.

T536's answer to T528 F-3 is `frozen_above` (default `T527`): `--write-baseline` refuses
to waive a finding whose task id sorts ABOVE that generation, or whose id it cannot place
in time. This script does not read that code -- it drives it.

Cells:
  A  synthetic incident under a task id nothing in this repo has ever used (T9001):
     --write-baseline must REFUSE it.
  B  anti-vacuity: a HISTORICAL id (T42) must still be waivable, else the control is
     just "refuse everything".
  C  the boundary is not moved by an ORDINARY REGENERATION: regenerate the shipped
     baseline and compare `frozen_above` before/after.
  D  DELETING the baseline does not lift the line: regenerate from nothing and check the
     freeze line that comes back.
  E  the id-form gap: `A2-999` is an id nothing has ever used either, but the A2
     generation sorts BELOW every T id, so `task_ordinal` dates it as history.
  F  the boundary itself: exactly T527 -- inclusive or exclusive?
  G  can `--write-baseline` be pointed at a FRESH file to escape the line?

Run:  python3 t537-freeze.py <path-to-worktree-at-18c64389>
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile

WT = sys.argv[1]
spec = importlib.util.spec_from_file_location(
    "cbp", os.path.join(WT, ".softhouse", "bin", "check-branch-published.py"))
cbp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cbp)

base = tempfile.mkdtemp(prefix="t537-freeze-")
T = lambda **kw: dict({"id": "TN", "status": "done"}, **kw)


def drive(name, tid, baseline_doc, expect_waived):
    d = os.path.join(base, name)
    os.makedirs(d)
    repo, f = cbp._fixture(d)
    cbp._write_tasks(repo, [T(id=tid, branch="softhouse/%s-never-pushed" % tid,
                              note="landed 1abd3a11 on softhouse/%s-never-pushed" % tid)])
    blp = os.path.join(repo, "bl.json")
    if baseline_doc is not None:
        with open(blp, "w") as fh:
            json.dump(baseline_doc, fh)
    res = cbp.check(repo, blp if os.path.exists(blp) else None, timeout=60)
    fa, fsrc = cbp.load_frozen_above(blp)
    ents, refs = cbp.write_baseline(repo, blp, res, fa, fsrc)
    waived = {e["subject"] for e in ents}
    br = "softhouse/%s-never-pushed" % tid
    got = br in waived
    ok = got == expect_waived
    print("%-44s id=%-9s freeze=%-6s(%s)  waived=%-5s want=%-5s  %s"
          % (name, tid, fa, fsrc, got, expect_waived, "PASS" if ok else "*** FAIL"))
    for t2, k, s, why in refs:
        print("      REFUSED %-9s %-40s %s" % (t2, s, why))
    return ok, ents, refs


print("=" * 78)
print("T537 item 3 -- BASELINE FREEZE, driven")
print("=" * 78)
print("module constant FROZEN_ABOVE = %r" % cbp.FROZEN_ABOVE)
print()

print("--- A. synthetic incident, id T9001 (nothing in this repo has ever used it)")
drive("A-T9001-above-the-line", "T9001", {"frozen_above": "T527", "waived": []}, False)
print()
print("--- B. anti-vacuity: a historical id must STILL be waivable")
drive("B-T42-historical", "T42", {"frozen_above": "T527", "waived": []}, True)
print()
print("--- E. id-form gap: A2-999, an id nothing has ever used, but an A2-SHAPED one")
drive("E-A2-999", "A2-999", {"frozen_above": "T527", "waived": []}, False)
print()
print("--- F. the boundary itself -- is T527 inclusive?")
drive("F-T527-exactly", "T527", {"frozen_above": "T527", "waived": []}, False)
print()
print("--- G. point --write-baseline at a FRESH file (no frozen_above in it)")
drive("G-fresh-baseline-file", "T9002", None, False)
print()

print("=" * 78)
print("--- C. ORDINARY REGENERATION must not move the line")
print("=" * 78)
shipped = os.path.join(WT, ".softhouse", "capture", "t527-branch-published",
                       "baseline.json")
work = os.path.join(base, "regen")
os.makedirs(work)
copy = os.path.join(work, "baseline.json")
shutil.copy(shipped, copy)
before = json.load(open(copy))
print("shipped frozen_above BEFORE: %r  (%d waivers)"
      % (before.get("frozen_above"), len(before["waived"])))
res = cbp.check(WT, copy, timeout=120)
fa, fsrc = cbp.load_frozen_above(copy)
ents, refs = cbp.write_baseline(WT, copy, res, fa, fsrc)
after = json.load(open(copy))
print("after ONE --write-baseline over the REAL record:")
print("  frozen_above AFTER : %r   (unchanged: %s)"
      % (after.get("frozen_above"), after.get("frozen_above") == before.get("frozen_above")))
print("  waivers written    : %d" % len(ents))
print("  findings REFUSED   : %d" % len(refs))
for t2, k, s, why in refs:
    print("     KEEP %-9s %-52s %s" % (t2, s, why))
newly = sorted({e["key"] for e in ents} - {e["key"] for e in before["waived"]})
print("  keys ADDED vs the shipped file: %d %s" % (len(newly), newly[:8]))

print()
print("=" * 78)
print("--- D. DELETING the baseline must not lift the line")
print("=" * 78)
work2 = os.path.join(base, "regen-deleted")
os.makedirs(work2)
gone = os.path.join(work2, "baseline.json")     # deliberately does not exist
fa2, fsrc2 = cbp.load_frozen_above(gone)
print("load_frozen_above(<missing file>) -> %r from %s" % (fa2, fsrc2))
res2 = cbp.check(WT, gone, timeout=120)
ents2, refs2 = cbp.write_baseline(WT, gone, res2, fa2, fsrc2)
doc2 = json.load(open(gone))
print("regenerated-from-nothing: frozen_above=%r, %d waivers, %d refused"
      % (doc2.get("frozen_above"), len(ents2), len(refs2)))
print("findings this regeneration REFUSED to launder:")
for t2, k, s, why in refs2:
    print("   KEEP %-9s %-52s %s" % (t2, s, why))
print()
print("findings this regeneration DID waive that the shipped file does not carry:")
newly2 = sorted({e["key"] for e in ents2} - {e["key"] for e in before["waived"]})
for k in newly2:
    print("   NEW  %s" % k.replace("\t", "  "))
if not newly2:
    print("   (none)")
