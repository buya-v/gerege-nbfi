#!/usr/bin/env python3
"""T451 -- the DECIDING measurement for C-T449-2, taken on the whole live ref store.

20-realrepo-census.py measured only the PATH axis and found 7 pairs that flip under
`anywhere`.  Driving the fixture then showed that a review branch whose COMMIT SUBJECT
names the reviewed task ("T981: review of T980") is already a CARRIER under the shipped
code, because the subject half is `anywhere` and always was.  So the path axis is not
where the question lives.  This instrument runs the WHOLE shipped
`ref_content_evidence` -- both halves -- over every (id, ref) pair the reconciler could
actually be asked about, and then the same pairs through the relaxed variant, and
reports the MARGINAL difference.

Three numbers matter and each is listed, not counted:
  * pairs that CARRY under the shipped code   (today's refusals)
  * pairs that CARRY only under `anywhere`    (what the proposal would ADD)
  * of each, how many are the task's OWN work vs somebody else's work naming it

usage: 21-realrepo-evidence.py [<repo>]
"""
import importlib.util, os, re, sys

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
TOOL = os.path.join(REPO, ".softhouse", "bin", "ready-tasks.py")
WORK = "/tmp/t451/mods"
os.makedirs(WORK, exist_ok=True)

src = open(TOOL, encoding="utf-8").read()
NEEDLE = """        parts = path.split("/")
        if any(leading.match(part) for part in parts):
            hits.append("path %s in the diff of %s vs main" % (path, ref))"""
RELAX = """        parts = path.split("/")
        if any(anywhere.search(part) for part in parts):
            hits.append("path %s in the diff of %s vs main" % (path, ref))"""
if src.count(NEEDLE) != 1:
    sys.exit("cannot plant the relaxation (%d sites) -- refusing to report a drive that "
             "did not run" % src.count(NEEDLE))
RELAXED = os.path.join(WORK, "rt_relaxed_census.py")
open(RELAXED, "w", encoding="utf-8").write(src.replace(NEEDLE, RELAX))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.set_repo(REPO)
    return m


ship = load(TOOL, "ship")
relx = load(RELAXED, "relx")

idx, note = ship.ref_index()
if idx is None:
    sys.exit("ref index unavailable: %s" % note)
ID = re.compile(r"(?<![0-9A-Za-z])((?:[Tt][0-9]+)|(?:A2-[0-9]+))(?![0-9A-Za-z])")
heads = {}
for n in sorted(idx.names()):
    short = ship.branch_sweep.short(n)
    hit = ID.search(short)
    if hit:
        heads.setdefault(hit.group(1).upper(), []).append(short)

carry_ship, carry_relx_only, clean = [], [], 0
pairs = 0
for tid in sorted(heads):
    for own in heads[tid]:
        refs, _ = ship.refs_naming(tid, own)
        for ref in refs or []:
            pairs += 1
            ev_s, ment_s, _ = ship.ref_content_evidence(tid, ref)
            ev_r, _, _ = relx.ref_content_evidence(tid, ref)
            short = ship.branch_sweep.short(ref)
            # is this ref OWNED by a DIFFERENT task?  the leading id of its own name.
            lead = ID.search(short.split("/")[-1])
            owner = lead.group(1).upper() if lead else "?"
            foreign = owner != tid
            if ev_s:
                carry_ship.append((tid, short, owner, foreign, ev_s[:1]))
            elif ev_r:
                carry_relx_only.append((tid, short, owner, foreign, ev_r[:1]))
            else:
                clean += 1

print("live refs %d ; ids nameable from a head %d ; (id, other-ref) pairs %d"
      % (len(idx.names()), len(heads), pairs))
print()
print("A. CARRY under the SHIPPED code -- these already REFUSE today: %d"
      % len(carry_ship))
for tid, short, owner, foreign, ev in carry_ship:
    print("   %-6s ref=%-46s ref-owner=%-6s %s" % (tid, short, owner,
                                                   "FOREIGN" if foreign else "own"))
    print("        %s" % ev[0][:150])
print()
print("B. CARRY only under the PROPOSED `anywhere` -- what the patch would ADD: %d"
      % len(carry_relx_only))
for tid, short, owner, foreign, ev in carry_relx_only:
    print("   %-6s ref=%-46s ref-owner=%-6s %s" % (tid, short, owner,
                                                   "FOREIGN" if foreign else "own"))
    print("        %s" % ev[0][:150])
print()
print("C. name-only under both: %d" % clean)
print()
fs = sum(1 for r in carry_ship if r[3])
fr = sum(1 for r in carry_relx_only if r[3])
print("FOREIGN-OWNED refs blocking a demotion:  shipped %d of %d   proposed adds %d of %d"
      % (fs, len(carry_ship), fr, len(carry_relx_only)))
