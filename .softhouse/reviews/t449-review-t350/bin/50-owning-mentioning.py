#!/usr/bin/env python3
"""T449 -- OWNING vs MENTIONING on the REAL repo, and the cases the rule DROPS.

Question 1: does the leading-anchor rule kill the T268 false positive?
Question 2: does it silently drop a task whose GENUINE work lives under another
            task's directory?  This program does that often (retry dirs, condition
            bundles, review dirs named for the reviewed task).
"""
import importlib.util, subprocess, sys, re, collections

REPO = sys.argv[1]
spec = importlib.util.spec_from_file_location("rt", "/tmp/t449/mods/rt_t350.py")
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
T.set_repo(REPO)

print("=== Q1: the T268 measurement the author says forced the leading anchor ===")
for tid in ("T268", "T286", "T291"):
    entries, _ = T.main_tree()
    own, men = T.paths_naming(tid, entries)
    print("\n  %s  OWNING=%d  MENTIONING=%d" % (tid, len(own), len(men)))
    dirs = collections.Counter()
    for p in men:
        parts = p.split("/")
        dirs["/".join(parts[:3])] += 1
    for d, n in dirs.most_common(6):
        print("      mention dir %-46s %d" % (d, n))
    ev, complete, _ = T.landed_evidence(tid)
    print("      landed_evidence -> flagged=%s complete=%s" % (bool(ev), complete))

print()
print("=== Q2: which tasks OWN nothing but are MENTIONED a lot? ===")
print("For each id nameable from a tracked path component, count OWNING and MENTIONING.")
entries, _ = T.main_tree()
IDRE = re.compile(r"(?<![0-9A-Za-z])([Tt]\d+)(?![0-9A-Za-z])")
seen = set()
for p, low in entries:
    for part in p.split("/"):
        for m in IDRE.finditer(part):
            seen.add(m.group(1).upper())
print("distinct T<n> ids nameable from a tracked path component on main: %d" % len(seen))
rows = []
for tid in sorted(seen):
    own, men = T.paths_naming(tid, entries)
    idx, _ = T.landed_index()
    subj = len(idx.get(tid, []))
    rows.append((len(own), len(men), subj, tid))
zero_own = [r for r in rows if r[0] == 0]
print("\nids with ZERO owning paths on main (the population the anchor could drop): %d"
      % len(zero_own))
for own, men, subj, tid in sorted(zero_own, key=lambda r: -r[1]):
    ev, _, _ = T.landed_evidence(tid)
    verdict = "FLAGGED (subject/handoff evidence)" if ev else "NOT FLAGGED"
    print("  %-6s owning=%d mentioning=%-3d landed_index_hits=%-2d -> %s"
          % (tid, own, men, subj, verdict))
