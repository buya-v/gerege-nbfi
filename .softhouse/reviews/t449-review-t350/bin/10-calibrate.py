#!/usr/bin/env python3
"""T449 independent calibration.

For EVERY local head in the real repo, ask main's _branch_wip_core and T350's
_branch_wip_core what they say, and cross-tabulate.  The task id is taken from the
branch's own short name (first T<digits> token, case-insensitive); heads with no id
are reported separately because neither code path can be exercised without one.
Written from the predicate; T350's own 40-calibrate.py was NOT read before this ran.
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


M = load("rt_main", "/tmp/t449/mods/rt_main.py")
T = load("rt_t350", "/tmp/t449/mods/rt_t350.py")


def g(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True,
                          text=True).stdout.strip()


heads = g("for-each-ref", "--format=%(refname:short)", "refs/heads").split()
print("local heads: %d" % len(heads))

IDRE = re.compile(r"(?<![0-9A-Za-z])(T\d+)(?![0-9A-Za-z])", re.IGNORECASE)
noid, rows = [], []
for h in heads:
    m = IDRE.search(h)
    if not m:
        noid.append(h)
        continue
    tid = m.group(1).upper()
    km, _ = M._branch_wip_core(h, tid)
    kt, _ = T._branch_wip_core(h, tid)
    rows.append((h, tid, km.split("/")[0], kt.split("/")[0]))

print("heads with NO T<n> id in the name (not exercised): %d" % len(noid))
for h in noid[:25]:
    print("   ", h)

tab = collections.Counter((r[2], r[3]) for r in rows)
print("\nRED(main kind) -> GREEN(T350 kind)   count   RED action / GREEN action")
for (a, b), n in sorted(tab.items()):
    print("  %-18s -> %-18s %4d   %-8s / %-8s" % (
        a, b, n,
        "REFUSE" if M.reconcile_action(a).startswith("REFUSE") else "demote",
        "REFUSE" if T.reconcile_action(b).startswith("REFUSE") else "demote"))

print("\n--- the pre-T350 `merged` population (0 ahead AND ancestor of main) ---")
merged = [r for r in rows if r[2] == "merged"]
print("heads main calls `merged`: %d" % len(merged))
keep = [r for r in merged if r[3] == "merged"]
flip = [r for r in merged if r[3] != "merged"]
print("  keep `merged`: %d" % len(keep))
print("  FLIP        : %d" % len(flip))
for h, tid, a, b in flip:
    print("    %-48s id=%-6s %s -> %s   head %s  %r"
          % (h, tid, a, b, g("rev-parse", "--short=9", h),
             g("log", "-1", "--format=%s", h)[:70]))

print("\n--- every REFUSE->demote transition, LISTED (P-80: list, do not count) ---")
n = 0
for h, tid, a, b in rows:
    if M.reconcile_action(a).startswith("REFUSE") and \
       not T.reconcile_action(b).startswith("REFUSE"):
        n += 1
        print("  REFUSE->demote  %-48s id=%-6s %s -> %s" % (h, tid, a, b))
print("  total REFUSE->demote: %d" % n)

print("\n--- every demote->REFUSE transition (the other direction) ---")
n = 0
for h, tid, a, b in rows:
    if T.reconcile_action(b).startswith("REFUSE") and \
       not M.reconcile_action(a).startswith("REFUSE"):
        n += 1
        print("  demote->REFUSE  %-48s id=%-6s %s -> %s" % (h, tid, a, b))
print("  total demote->REFUSE: %d" % n)
