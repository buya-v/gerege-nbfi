#!/usr/bin/env python3
"""Why my 157 and T350's 175 are the same measurement of different populations.

Re-runs the SAME cross-tab with T350's id regex (which admits `A2-10`, not only
`T<digits>`), and separately reports the state of the two heads T350 said flipped.
"""
import importlib.util, re, subprocess, sys

REPO = sys.argv[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    m.set_repo(REPO)
    return m


M = load("rt_main", "/tmp/t449/mods/rt_main.py")
T = load("rt_t350", "/tmp/t449/mods/rt_t350.py")


def g(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True,
                          text=True).stdout.strip()


heads = g("for-each-ref", "--format=%(refname:short)", "refs/heads").split()
THEIRS = re.compile(r"(?<![0-9A-Za-z])([A-Za-z]+-?T?\d+(?:-\d+)?)(?![0-9A-Za-z])")

pop, noid = [], []
for h in heads:
    if g("rev-list", "--count", "main.." + h) != "0":
        continue
    if subprocess.run(["git", "merge-base", "--is-ancestor", h, "main"], cwd=REPO,
                      capture_output=True).returncode != 0:
        continue
    m = THEIRS.search(h.split("/")[-1])
    if not m:
        noid.append(h)
        continue
    pop.append((h, m.group(1)))

print("T350's population definition (0 ahead AND ancestor, id parsed from last")
print("path component with T350's own regex): %d heads, %d unparseable"
      % (len(pop), len(noid)))
kept, flipped, unver = [], [], []
for h, tid in pop:
    ev, complete, _ = T.landed_evidence(tid)
    if ev:
        kept.append((h, tid))
    elif not complete:
        unver.append((h, tid))
    else:
        flipped.append((h, tid))
print("  keep `merged`      : %d" % len(kept))
print("  merged-unverified  : %d" % len(unver))
print("  FLIP to stillborn  : %d" % len(flipped))
for h, tid in flipped:
    print("     %-52s id=%-9s %s" % (h, tid, g("log", "-1", "--format=%h %s", h)[:70]))

print()
print("--- the two heads T350 reported as flips, today ---")
for pat in ("T350", "T412"):
    for h in heads:
        if pat in h:
            n = g("rev-list", "--count", "main.." + h)
            anc = subprocess.run(["git", "merge-base", "--is-ancestor", h, "main"],
                                 cwd=REPO, capture_output=True).returncode
            km, _ = M._branch_wip_core(h, pat)
            kt, _ = T._branch_wip_core(h, pat)
            print("  %-48s ahead=%-3s ancestor_rc=%s  main:%-8s T350:%-8s  head %s"
                  % (h, n, anc, km, kt, g("rev-parse", "--short=9", h)))
