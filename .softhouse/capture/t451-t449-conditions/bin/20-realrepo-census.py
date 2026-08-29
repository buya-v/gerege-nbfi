#!/usr/bin/env python3
"""T451 -- what do the two ref-side repairs COST on the real repo, today?

Two questions, both asked of the real ref store rather than of a fixture:

  (1) C-T449-2.  For every id nameable from a local head, take the OTHER live refs whose
      NAME carries that id -- i.e. exactly the population `refs_carrying_content` probes
      -- and ask each one under BOTH anchors: does its own diff vs main contain a path
      component that BEGINS with the id (shipped), and does it contain one that NAMES
      the id ANYWHERE (proposed)?  A ref that flips name-only -> carrier turns a DEMOTE
      into a REFUSE, so every flip is listed, not counted.

  (2) C-T449-5.  What is the real fan-out?  How many ids have more name-matching refs
      than the shipped cap of 8, i.e. how many are exposed to the truncation today?

Nothing here is a fixture.  "0 flips" would be a fact about this repo on this day, and
is reported as such -- it is not a statement that the shape cannot occur.
"""
import importlib.util, os, re, sys, collections

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
TOOL = os.path.join(REPO, ".softhouse", "bin", "ready-tasks.py")

spec = importlib.util.spec_from_file_location("rt", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.set_repo(REPO)

idx, note = m.ref_index()
if idx is None:
    sys.exit("ref index unavailable: %s" % note)
names = sorted(idx.names())
print("live refs in the store: %d" % len(names))

ID = re.compile(r"(?<![0-9A-Za-z])((?:[Tt][0-9]+)|(?:A2-[0-9]+))(?![0-9A-Za-z])")
heads = {}
for n in names:
    short = m.branch_sweep.short(n)
    hit = ID.search(short)
    if hit:
        heads.setdefault(hit.group(1).upper(), []).append(short)
print("ids nameable from a local head: %d" % len(heads))

fanout = collections.Counter()
flips, probed, over_cap = [], 0, []
for tid in sorted(heads):
    for own in heads[tid]:
        refs, _ = m.refs_naming(tid, own)
        if refs is None:
            continue
        fanout[len(refs)] += 1
        if len(refs) > m.MAX_REFS_PROBED:
            over_cap.append((tid, own, len(refs)))
        for ref in refs:
            probed += 1
            anywhere, leading = m.id_pattern(tid)
            rc, out, _ = m._run([m.GIT, "diff", "--name-only", "main...%s" % ref], 15)
            if rc != 0:
                continue
            paths = out.splitlines()
            lead = [p for p in paths
                    if any(leading.match(part) for part in p.split("/"))]
            anyw = [p for p in paths
                    if any(anywhere.search(part) for part in p.split("/"))]
            if anyw and not lead:
                flips.append((tid, own, m.branch_sweep.short(ref), anyw[:3]))

print("(id, own-head) pairs examined     : %d" % sum(fanout.values()))
print("ref probes run                    : %d" % probed)
print("fan-out histogram (other refs naming the id): %s"
      % dict(sorted(fanout.items())))
print("MAX fan-out on this repo today    : %d   (shipped cap MAX_REFS_PROBED=%d)"
      % (max(fanout) if fanout else 0, m.MAX_REFS_PROBED))
print("ids AT OR OVER the cap today      : %d" % len(over_cap))
for t in over_cap:
    print("    %s" % (t,))
print()
print("C-T449-2 -- refs that flip name-only -> CARRIER under `anywhere`: %d" % len(flips))
for tid, own, ref, paths in flips:
    print("    %-8s own=%-46s ref=%s" % (tid, own, ref))
    for p in paths:
        print("        %s" % p)
if not flips:
    print("    NONE on this repo today.  This is a statement about THIS ref store on")
    print("    2026-08-29, not about the shape: the shape needs a sweep-rescued ref that")
    print("    survived, and the sweep deletes nothing, so it accumulates.")
