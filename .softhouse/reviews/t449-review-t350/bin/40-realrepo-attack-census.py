#!/usr/bin/env python3
"""T449 -- is the G/ATTACK shape and the H/CAP shape REACHABLE ON THE REAL REPO?

G-shape: a task id for which
   (a) some live ref CARRIES content owning the id (T350's own ref_content_evidence),
   (b) NOTHING owning the id is on main, and
   (c) a branch whose name owns the id still exists, 0 ahead of main and an ancestor
       of main -- i.e. `_branch_wip_core` will answer `stillborn` and DEMOTE without
       ever asking (a).

H-shape: how many live refs name any one id?  MAX_REFS_PROBED is 8.
"""
import importlib.util, re, subprocess, sys, collections

REPO = sys.argv[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    m.set_repo(REPO)
    return m


T = load("rt_t350", "/tmp/t449/mods/rt_t350.py")


def g(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True,
                          text=True).stdout.strip()


heads = g("for-each-ref", "--format=%(refname:short)", "refs/heads").split()
IDRE = re.compile(r"(?<![0-9A-Za-z])(T\d+)(?![0-9A-Za-z])", re.IGNORECASE)

# ---------------------------------------------------------------- H: ref fan-out ----
ids = sorted({m.group(1).upper() for h in heads for m in [IDRE.search(h)] if m})
print("distinct T<n> ids nameable from local head names: %d" % len(ids))
fan = []
for tid in ids:
    refs, _ = T.refs_naming(tid, None)
    fan.append((len(refs or []), tid, [T.branch_sweep.short(r) for r in (refs or [])]))
fan.sort(reverse=True)
print("\nH/CAP -- ids by number of NAME-MATCHING live refs (cap = %d):"
      % T.MAX_REFS_PROBED)
for n, tid, rr in fan[:12]:
    mark = "  <== AT OR OVER THE CAP" if n >= T.MAX_REFS_PROBED else ""
    print("  %-6s %2d%s" % (tid, n, mark))
    if n >= T.MAX_REFS_PROBED:
        for r in rr:
            print("        %s" % r)
over = [t for n, t, _ in fan if n > T.MAX_REFS_PROBED]
print("  ids ABOVE the cap today: %d %s" % (len(over), over))
print("  max fan-out observed: %d" % (fan[0][0] if fan else 0))

# ---------------------------------------------------------------- G: the shape ------
print()
print("G/ATTACK -- live instances of 'ref carries content, nothing on main, recorded")
print("branch still parked at the dispatch commit' (the state where the ref is NEVER")
print("consulted).  Every id with a live head naming it is tested.")
hits = 0
for tid in ids:
    ev, complete, _ = T.landed_evidence(tid)
    if ev or not complete:
        continue                       # something owning it IS on main -> `merged`
    # every branch whose name owns this id, that is 0-ahead and an ancestor of main
    stillborn_branches = []
    for h in heads:
        m = IDRE.search(h)
        if not m or m.group(1).upper() != tid:
            continue
        kind, _ = T._branch_wip_core(h, tid)
        if kind.split("/")[0] == "stillborn":
            stillborn_branches.append(h)
    if not stillborn_branches:
        continue
    carriers, name_only, unprobed, _ = T.refs_carrying_content(tid, None)
    if carriers:
        hits += 1
        print("\n  !! %s" % tid)
        for b in stillborn_branches:
            print("       DEMOTED as `stillborn`: %s @ %s" % (b, g("rev-parse", "--short=9", b)))
        for r, e in carriers:
            print("       BUT THIS REF CARRIES CONTENT: %s" % T.branch_sweep.short(r))
            for x in e[:3]:
                print("          %s" % x)
    else:
        print("  ok %-6s stillborn on %s, and no ref carries content either"
              % (tid, stillborn_branches))
print("\nlive G-shape instances on the real repo right now: %d" % hits)
