#!/usr/bin/env python3
"""T451 -- drive `branch_wip` + `reconcile_action` over the fixture, RED vs GREEN.

RED  is loaded BY PATH from a file the caller names (normally `git show main:...`).
GREEN is loaded BY PATH from the working-tree file.
Both are loaded FRESH per case, because the module caches `_LANDED`, `_MAINTREE`,
`_REF_INDEX` and `_IDPAT` in globals and a stale cache would make the second case in a
run answer the first case's question.

usage: 11-drive.py <fixture-dir> <red.py> <green.py> [--json out.json]
"""
import importlib.util, json, os, sys, hashlib

CASES = [
    # (label, task id, recorded branch, what it is, what MUST happen)
    ("A/T339 ", "T339", "softhouse/T339-base",
     "INCIDENT ref: name matches, its diff is another task's deletion + T347 marker",
     "MUST STAY name-only-refs/DEMOTE -- relaxing the ref anchor must not resurrect it"),
    ("B/T431 ", "T431", "softhouse/T431-t407-conditions",
     "task branch parked AT the dispatch commit, nothing anywhere",
     "MUST STAY stillborn/DEMOTE -- this is the case T350 was filed for"),
    ("C/T421 ", "T421", "softhouse/T421-t406-conditions",
     "branch pruned after merge, OWNING paths on main",
     "MUST STAY merged/REFUSE"),
    ("D/T428 ", "T428", "softhouse/T428-review-t421",
     "branch pruned after merge, review dir on main, subject is a Merge line",
     "MUST STAY merged/REFUSE"),
    ("E/T351 ", "T351", "softhouse/T351-progress-accounting",
     "MUST-BLOCK control: branch RENAMED, ref carries real OWNING content",
     "MUST STAY relocated/REFUSE"),
    ("G/T900 ", "T900", "softhouse/T900-work",
     "ATTACK: task branch parked at dispatch commit AND a rescue ref carries the work",
     "C-T449-1: must REFUSE.  RED demotes while a live ref holds the line"),
    ("G2/T901", "T901", "softhouse/T901-work",
     "CONTROL for G: byte-identical evidence, recorded branch DELETED",
     "relocated/REFUSE in both -- G and G2 must now AGREE"),
    ("K/T945 ", "T945", "softhouse/T945-t944-conditions",
     "C-T449-2: work under ANOTHER task's condition-bundle dir, branch deleted",
     "STAYS name-only-refs/DEMOTE -- re-derived, see 13-relaxed-probe: relaxing the "
     "anchor to fix this costs 7 FALSE REFUSALS on the live repo and buys 0.  What "
     "must change is the NOTE, which used to deny the path exists"),
    ("K2/T946", "T946", "softhouse/T946-t944-conditions",
     "C-T449-2 with the task branch still parked (the C-T449-1 leg too)",
     "STAYS DEMOTE, same reasoning; the note must name the mentioning path"),
    ("R/T980 ", "T980", "softhouse/T980-work",
     "THE COST OF THE PROPOSED RELAXATION: a live ref carrying T981's REVIEW OF T980",
     "MUST STAY name-only-refs/DEMOTE.  `anywhere` would REFUSE here -- 7 live pairs"),
    ("S/T990 ", "T990", "softhouse/T990-shared-file",
     "RESIDUAL: rescue ref whose diff touches only a SHARED file, naming no id at all",
     "DEMOTES under BOTH anchors -- neither fix closes this; recorded, not closed"),
    ("H/T950 ", "T950", "softhouse/T950-real",
     "ATTACK: 9 name-matching refs, the only carrier LAST in sort order",
     "C-T449-5: must REFUSE.  RED truncates at the cap and demotes"),
    ("N/T960 ", "T960", "softhouse/T960-work",
     "CONTROL: stillborn task branch + a NAME-ONLY ref",
     "MUST STAY DEMOTE, but the note must NAME the ref, not deny it"),
    ("P/T970 ", "T970", "softhouse/T970-nothing",
     "CONTROL: truly unstarted -- branch parked, no refs, nothing on main",
     "MUST STAY stillborn/DEMOTE"),
]


def load(path, repo, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.set_repo(repo)
    return mod


def drive(path, repo, tag):
    out = {}
    for i, (label, tid, branch, _what, _must) in enumerate(CASES):
        mod = load(path, repo, "%s_%d" % (tag, i))
        kind, text = mod.branch_wip(branch, tid)
        act = mod.reconcile_action(kind)
        out[label] = (kind, act.split(" --")[0].split(" to ")[0].strip(), text)
    return out


def main():
    fix, red, green = sys.argv[1], sys.argv[2], sys.argv[3]
    print("RED   %s  sha256 %s" % (red, hashlib.sha256(open(red, "rb").read()).hexdigest()[:16]))
    print("GREEN %s  sha256 %s" % (green, hashlib.sha256(open(green, "rb").read()).hexdigest()[:16]))
    print("fixture %s\n" % fix)
    R = drive(red, fix, "red")
    G = drive(green, fix, "green")
    changed = 0
    for label, tid, branch, what, must in CASES:
        rk, ra, rt = R[label]
        gk, ga, gt = G[label]
        flag = "  <== CHANGED" if (rk, ra) != (gk, ga) else ""
        if flag:
            changed += 1
        print("%s  %s" % (label, what))
        print("          expectation: %s" % must)
        print("          RED    %-22s %s" % (rk, ra.upper()))
        print("          GREEN  %-22s %s%s" % (gk, ga.upper(), flag))
        print()
    print("cases: %d, changed: %d" % (len(CASES), changed))
    print("\n" + "=" * 78)
    print("VERBATIM NOTES -- the record a human reads before deciding")
    print("=" * 78)
    for label in ("G/T900 ", "K/T945 ", "N/T960 ", "A/T339 ", "S/T990 "):
        for tag, tbl in (("RED  ", R), ("GREEN", G)):
            print("\n--- %s %s [%s] ---\n%s" % (tag, label, tbl[label][0], tbl[label][2]))
    if len(sys.argv) > 5 and sys.argv[4] == "--json":
        with open(sys.argv[5], "w") as fh:
            json.dump({"red": {k: v[:2] for k, v in R.items()},
                       "green": {k: v[:2] for k, v in G.items()}}, fh, indent=1)


main()
