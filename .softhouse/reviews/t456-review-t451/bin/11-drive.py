#!/usr/bin/env python3
"""T456 -- drive RED, GREEN and the T449-RELAXED variant over the reviewer's own fixture.

Every module is loaded BY PATH and `set_repo()`d at the fixture, so the bytes under test
are the bytes on the branch, never a paraphrase.  The relaxed variant is planted here
(one site, verified unique before writing) rather than borrowed from T451.

usage: 11-drive.py <red.py> <green.py> <fixture-dir> <workdir>
"""
import importlib.util
import os
import shutil
import sys

RED, GREEN, FIX, WORK = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(WORK, exist_ok=True)

# ---- plant the T449 relaxation into GREEN, one site, verified unique ----------------
# The REF side only.  There are TWO structurally identical anchors in this module -- the
# main-side one in `paths_naming()` and the ref-side one in `ref_content_evidence()` --
# and T449's patch is about the SECOND.  The needle therefore carries the ref-side
# `hits.append` line, and the count check below refused loudly when a shorter needle
# matched both.  That refusal is the instrument working.
NEEDLE = """        parts = path.split("/")
        if any(leading.match(part) for part in parts):
            hits.append("path %s in the diff of %s vs main" % (path, ref))"""
RELAX = """        parts = path.split("/")
        if any(anywhere.search(part) for part in parts):
            hits.append("path %s in the diff of %s vs main" % (path, ref))"""
src = open(GREEN, encoding="utf-8").read()
if src.count(NEEDLE) != 1:
    sys.exit("ABORT: %d sites for the relaxation, expected 1. Refusing to report a drive "
             "that did not plant." % src.count(NEEDLE))
RELAXED = os.path.join(WORK, "rt_relaxed.py")
open(RELAXED, "w", encoding="utf-8").write(src.replace(NEEDLE, RELAX))
for mod in (RED, GREEN):
    bs = os.path.join(os.path.dirname(mod), "branch_sweep.py")
    if os.path.exists(bs):
        shutil.copy(bs, os.path.join(WORK, "branch_sweep.py"))
        break
if not os.path.exists(os.path.join(WORK, "branch_sweep.py")):
    sys.exit("ABORT: branch_sweep.py not stageable beside the relaxed copy; every ref "
             "verdict below would be an artefact.")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if getattr(m, "branch_sweep", "x") is None:
        sys.exit("ABORT: %s could not import branch_sweep (%s)" % (path, m.BRANCH_SWEEP_ERR))
    m.set_repo(FIX)
    return m


CASES = [
    # (label, recorded branch, tid, what it is)
    ("G/T900",   "softhouse/T900-work",                 "T900",
     "branch parked at dispatch AND a rescue ref carries the work"),
    ("G2/T901",  "softhouse/T901-work",                 "T901",
     "same evidence, recorded branch DELETED"),
    ("R2/T982",  "softhouse/T982-review-target",        "T982",
     "a swept REVIEWER worktree; boilerplate subject; path is T983's review OF T982"),
    ("K/T945",   "softhouse/T945-t944-conditions",      "T945",
     "T449 case K: work under another id's dir, filename names nobody"),
    ("KOWN/T947", "softhouse/T947-t944-conditions",     "T947",
     "case K WITH this program's filename convention (the live T428 shape)"),
    ("S/T990",   "softhouse/T990-shared-file",          "T990",
     "rescue ref touching only a SHARED file -- names no id at all"),
    ("HLOAD/T955", "softhouse/T955-decoy-target",       "T955",
     "2 name-matching refs, the only carrier SECOND in sort order"),
    ("E/T351",   "softhouse/T351-progress-accounting",  "T351",
     "MUST-BLOCK control: live ref, real OWNING content, branch renamed"),
]

legs = [("RED   ", load(RED, "m_red")),
        ("GREEN ", load(GREEN, "m_green")),
        ("RELAX ", load(RELAXED, "m_relax"))]

print("fixture           : %s" % FIX)
print("RED               : %s" % RED)
print("GREEN             : %s" % GREEN)
print("RELAX (T449 patch): %s   [planted here, 1 site]" % RELAXED)
print()
rows = {}
for label, branch, tid, what in CASES:
    print("=" * 92)
    print("%-12s %s" % (label, what))
    print("             recorded branch %s" % branch)
    for tag, m in legs:
        m._MAINTREE = ("uncached", None)
        m._REF_INDEX = ("uncached", None)
        m._IDPAT = {}
        kind, text = m.branch_wip(branch, tid)
        action = m.reconcile_action(kind)
        pol = "REFUSE" if action.startswith("REFUSE") else "demote"
        rows[(label, tag.strip())] = (kind, pol)
        print("   %s %-22s %-7s" % (tag, kind, pol))
        print("        %s" % text.replace("\n", " ")[:600])
    print()

print("=" * 92)
print("SUMMARY -- kind / polarity")
print("=" * 92)
print("%-12s %-30s %-30s %-30s" % ("case", "RED", "GREEN", "RELAXED (T449)"))
for label, _b, _t, _w in CASES:
    cells = []
    for tag in ("RED", "GREEN", "RELAX"):
        k, p = rows[(label, tag)]
        cells.append("%s %s" % (k, p))
    mark = ""
    if rows[(label, "GREEN")][1] != rows[(label, "RED")][1]:
        mark += "   <== GREEN CHANGED"
    if rows[(label, "RELAX")][1] != rows[(label, "GREEN")][1]:
        mark += "   <== T449's PATCH CHANGES THIS"
    print("%-12s %-30s %-30s %-30s%s" % (label, cells[0], cells[1], cells[2], mark))
