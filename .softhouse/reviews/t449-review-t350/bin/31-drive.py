#!/usr/bin/env python3
"""T449 -- drive main's bytes (RED) and T350's bytes (GREEN) over the fixture.

Both modules are loaded BY PATH.  RED is the sha256-verified copy of what is on
`main` today; GREEN is `git show softhouse/T350-reconcile-content:...`.
"""
import importlib.util, sys, hashlib

REPO = "/tmp/t449/fixture"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    m.set_repo(REPO)
    return m


for p in ("/tmp/t449/mods/rt_main.py", "/tmp/t449/mods/rt_t350.py"):
    print("%s  sha256 %s" % (p, hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]))
M = load("rt_main", "/tmp/t449/mods/rt_main.py")
T = load("rt_t350", "/tmp/t449/mods/rt_t350.py")
print("branch_sweep imported: RED=%s GREEN=%s\n"
      % (M.branch_sweep is not None, T.branch_sweep is not None))

CASES = [
    ("A/T339  name-only rescue ref, nothing of T339 anywhere",
     "softhouse/T339-recorded", "T339"),
    ("B/T431  branch parked AT the dispatch commit, nothing landed",
     "softhouse/T431-t407-conditions", "T431"),
    ("C/T421  branch gone, 2 files + `T421:` subject ON MAIN",
     "softhouse/T421-t406-conditions", "T421"),
    ("D/T428  branch gone, review dir + `T428:` subject ON MAIN",
     "softhouse/T428-review-t421", "T428"),
    ("E/T351  CONTROL must block: live ref CARRIES real t351 content",
     "softhouse/T351-recorded", "T351"),
    ("F/T442  CONTROL must block: live ref CARRIES real t442 content",
     "softhouse/T442-recorded", "T442"),
    ("G/ATTACK  rescue ref CARRIES real t900 content AND the recorded branch"
     " STILL EXISTS at the dispatch commit",
     "softhouse/T900-work", "T900"),
    ("G2/CONTROL identical rescue ref, recorded branch DELETED",
     "softhouse/T901-work", "T901"),
    ("H/CAP  9 name-matching refs; only `zz-t950-real` (LAST in sort order) carries"
     " content; MAX_REFS_PROBED=%d" % T.MAX_REFS_PROBED,
     "softhouse/T950-recorded", "T950"),
    ("J/NO-OWNING-PATH  work landed as nexus/ledger/posting.go under subject"
     " `softhouse: T870+T871 merged`", "softhouse/T870-work", "T870"),
]

print("=" * 100)
print("%-70s %-19s %-19s" % ("case", "RED (main)", "GREEN (T350)"))
print("=" * 100)
notes = []
for label, branch, tid in CASES:
    km, tm = M.branch_wip(branch, tid)
    kt, tt = T.branch_wip(branch, tid)
    am = "REFUSE" if M.reconcile_action(km).startswith("REFUSE") else "DEMOTE"
    at = "REFUSE" if T.reconcile_action(kt).startswith("REFUSE") else "DEMOTE"
    flag = "   <== CHANGED" if am != at else ""
    print("%-70s %-12s %-6s %-12s %-6s%s"
          % (label[:70], km.split("/")[0], am, kt.split("/")[0], at, flag))
    notes.append((label, branch, tid, km, tm, kt, tt))

print()
print("=" * 100)
print("VERDICT TEXT, VERBATIM, for the cases that matter")
print("=" * 100)
for label, branch, tid, km, tm, kt, tt in notes:
    if not label.startswith(("G/", "G2/", "H/", "J/", "E/")):
        continue
    print("\n### %s\n  branch=%s tid=%s" % (label, branch, tid))
    print("  RED   [%s]\n    %s" % (km, tm.replace("\n", "\n    ")))
    print("  GREEN [%s]\n    %s" % (kt, tt.replace("\n", "\n    ")))

# ---------------------------------------------------------------- the READY flag ----
print()
print("=" * 100)
print("landed_evidence() -- the READY-listing flag (OWNING vs MENTIONING)")
print("=" * 100)
for tid in ("T268", "T286", "T421", "T428", "T351", "T870", "T900"):
    ev, complete, note = T.landed_evidence(tid)
    print("\n  %s  flagged=%s complete=%s" % (tid, bool(ev), complete))
    for e in ev:
        print("      EV: %s" % e)
    print("      note: %s" % note[:400])

# ---------------------------------------------------------------- the ref probe -----
print()
print("=" * 100)
print("refs_carrying_content() -- what the cap does")
print("=" * 100)
for tid, excl in (("T950", "softhouse/T950-recorded"),
                  ("T900", "softhouse/T900-work"),
                  ("T339", "softhouse/T339-recorded")):
    c, n, u, note = T.refs_carrying_content(tid, excl)
    print("\n  %s  carriers=%s" % (tid, [r for r, _ in (c or [])]))
    print("      name_only=%s" % n)
    print("      unprobed=%s" % u)
    print("      note: %s" % note[:600])
