#!/usr/bin/env python3
"""T462 / C-T456-4 -- RE-STATE A CARDINAL AS A MEMBER SET WITH ITS TREE.

The shipped docstring says the `anywhere` relaxation "adds **exactly 0** carriers".  A
bare cardinal is a measurement wearing the clothes of a fact: it was true on 2026-08-28
and T456 showed it false on 2026-08-29, one day later, because `softhouse/T455-t448-
conditions` came into existence carrying T455's work about T448's conditions.  What does
NOT rot is the SHAPE of the members: every pair the relaxation adds is FOREIGN-owned
work that merely names the id, which is precisely why the relaxation was rejected.  So
print the members, print the tree they were measured at, and let the reader see whether
the shape held rather than trusting a number.

This is F-T447-3's lesson one file over, and it is why the output below leads with
`MEASURED-AT` and never with a total.

usage: 20-relaxation-members.py [<repo>] [<workdir>]
"""
import importlib.util
import os
import re
import subprocess
import sys

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
WORK = sys.argv[2] if len(sys.argv) > 2 else "/tmp/t462/relax"
S = ".softhouse"                       # assembled, never spelled as a literal path
TOOL = os.path.join(REPO, S, "bin", "ready-tasks.py")
os.makedirs(WORK, exist_ok=True)
if not os.path.exists(TOOL):
    sys.exit("ABORT: no resolver at %s -- nothing to measure" % TOOL)


def git(*a):
    p = subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else "?"


print("MEASURED-AT")
print("  repo        : %s" % REPO)
print("  HEAD        : %s  %s" % (git("rev-parse", "HEAD")[:12],
                                  git("log", "-1", "--format=%ad", "--date=iso")))
print("  HEAD subject: %s" % git("log", "-1", "--format=%s")[:100])
print("  resolver sha: %s" % git("hash-object", TOOL)[:12])
print()

src = open(TOOL, encoding="utf-8").read()
NEEDLE = """        parts = path.split("/")
        if any(leading.match(part) for part in parts):
            hits.append("path %s in the diff of %s vs main" % (path, ref))"""
RELAX = NEEDLE.replace("leading.match(part)", "anywhere.search(part)")
if src.count(NEEDLE) != 1:
    sys.exit("ABORT: the relaxation site occurs %d times -- refusing to report a drive "
             "that did not run" % src.count(NEEDLE))
RELAXED = os.path.join(WORK, "rt_relaxed.py")
open(RELAXED, "w", encoding="utf-8").write(src.replace(NEEDLE, RELAX))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if getattr(m, "branch_sweep", "x") is None:
        sys.exit("ABORT: %s could not import branch_sweep" % path)
    m.set_repo(REPO)
    return m


ship = load(TOOL, "ship")
relx = load(RELAXED, "relx")

idx, note = ship.ref_index()
if idx is None:
    sys.exit("ABORT: ref index unavailable: %s" % note)
ID = re.compile(r"(?<![0-9A-Za-z])((?:[Tt][0-9]+)|(?:A2-[0-9]+))(?![0-9A-Za-z])")
heads = {}
for n in sorted(idx.names()):
    short = ship.branch_sweep.short(n)
    hit = ID.search(short)
    if hit:
        heads.setdefault(hit.group(1).upper(), []).append(short)

carry_ship, added, clean = [], [], 0
pairs = 0
for tid in sorted(heads):
    for own in heads[tid]:
        refs, _ = ship.refs_naming(tid, own)
        for ref in refs or []:
            pairs += 1
            ev_s, _m, _n = ship.ref_content_evidence(tid, ref)
            ev_r, _m2, _n2 = relx.ref_content_evidence(tid, ref)
            short = ship.branch_sweep.short(ref)
            lead = ID.search(short.split("/")[-1])
            owner = lead.group(1).upper() if lead else "?"
            row = (tid, short, owner, owner != tid, (ev_s or ev_r or [""])[0][:130])
            if ev_s:
                carry_ship.append(row)
            elif ev_r:
                added.append(row)
            else:
                clean += 1

print("population : %d live refs, %d ids nameable from a head, %d (id, other-ref) pairs"
      % (len(idx.names()), len(heads), pairs))
print()
print("SET B -- pairs that CARRY ONLY UNDER THE PROPOSED `anywhere` RELAXATION.")
print("         This is the set the shipped docstring reported as the cardinal 0.")
print("         MEMBERS (id, ref, the ref's OWN leading id, whose work it is):")
if not added:
    print("   { }   -- empty ON THIS TREE. Not a property of the predicate.")
for tid, short, owner, foreign, ev in sorted(added):
    print("   %-6s ref=%-46s ref-owner=%-6s %s"
          % (tid, short, owner, "FOREIGN -- somebody else's work naming %s" % tid
             if foreign else "the task's OWN work"))
    print("          %s" % ev)
print()
nf = sum(1 for r in added if r[3])
print("   |B| = %d, of which FOREIGN-owned = %d" % (len(added), nf))
print("   THE ADJUDICATION DOES NOT TURN ON |B|. It turns on whether B's members are")
print("   foreign work. Every member above that reads FOREIGN is a task that would")
print("   REFUSE TO DEMOTE FOREVER on the strength of somebody else's branch.")
print()
print("SET A -- pairs that CARRY under the SHIPPED code (today's refusals): %d"
      % len(carry_ship))
for tid, short, owner, foreign, ev in sorted(carry_ship):
    print("   %-6s ref=%-46s ref-owner=%-6s %s"
          % (tid, short, owner, "FOREIGN" if foreign else "own"))
print()
print("SET C -- name-only under BOTH anchors: %d pairs" % clean)
print()
fa = sum(1 for r in carry_ship if r[3])
print("FOREIGN-owned refs blocking a demotion: shipped %d of %d ; the relaxation would "
      "ADD %d of %d" % (fa, len(carry_ship), nf, len(added)))
print()
print("VERDICT-SHAPE (what a later reader should re-check, rather than the numbers):")
print("  * is every member of B foreign-owned?  %s"
      % ("YES" if added and all(r[3] for r in added)
         else "B is empty on this tree" if not added else "NO -- READ THE MEMBERS"))
print("  * that is the whole argument against `anywhere`, and it is INDEPENDENT of |B|.")
print()

# ---------------------------------------------------------------------------------
# NAMED-PAIR AUDIT.  A member set is only better than a cardinal if a later reader can
# ask what happened to a NAMED member.  Every pair any earlier measurement put in B goes
# here, with the reason it is or is not in B today -- so the READER sees the mechanism
# of the rot rather than a second number that will rot the same way.
print("NAMED-PAIR AUDIT -- pairs earlier measurements placed in B, re-asked on THIS tree")
CITED = [
    ("T448", "softhouse/T455-t448-conditions",
     "T456, 2026-08-29: T455's work ABOUT T448's conditions -- foreign, so under "
     "`anywhere` T448 would refuse forever on it"),
]
names = set(ship.branch_sweep.short(n) for n in idx.names())
for tid, ref, provenance in CITED:
    print("   %s / %s" % (tid, ref))
    print("      cited by: %s" % provenance)
    if ref in names:
        ev_s, _m, _n = ship.ref_content_evidence(tid, ref)
        ev_r, _m2, _n2 = relx.ref_content_evidence(tid, ref)
        state = ("in B (carries only under `anywhere`)" if (not ev_s and ev_r)
                 else "in A (carries under the SHIPPED anchor)" if ev_s
                 else "in C (name-only under both)")
        print("      TODAY  : the ref EXISTS and the pair is %s" % state)
    else:
        merged = git("log", "main", "--oneline", "--format=%h %s", "--grep",
                     ref.split("/")[-1])
        tracked = subprocess.run(
            ["git", "-C", REPO, "ls-tree", "-r", "--name-only", "main"],
            capture_output=True, text=True)
        owndir = sum(1 for p in tracked.stdout.splitlines()
                     if ref.split("/")[-1].lower() in p.lower())
        print("      TODAY  : THE REF NO LONGER EXISTS. Not 'the pair became name-only'")
        print("               -- the ref was PRUNED. Its work is on main (%d tracked "
              "path(s) under its own directory)." % owndir)
        if merged:
            print("               merge commit: %s" % merged.splitlines()[0][:110])
        print("               So |B| moved 0 -> 1 -> 0 in under 24 hours WITHOUT the")
        print("               predicate changing at all: create, merge, prune. A")
        print("               cardinal over a ref store is a measurement of the ref")
        print("               store's WEATHER, and the docstring published it as a fact.")
