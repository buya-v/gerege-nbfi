#!/usr/bin/env python3
"""Does the SMALL fix close the seven breaks, and keep the legitimate case green?"""
import sys, os, importlib.util
sys.argv = [sys.argv[0], sys.argv[1]]
import measure2 as M   # reuses landing_shas / the veto rules (its own run already printed)

CASES = [
    ("A-merge-base-plain",       "done and scope-checked (merge base SHA)",              False),
    ("B-merge-base-COMMIT",      "done; merge-base commit SHA, scope clean",             False),
    ("C-branched-from-at",       "branched from main @ SHA; work is on the branch",      False),
    ("E-base-branch-paren",      "based on softhouse/TOTHER-x (SHA) -- stacked on top",  False),
    ("G-review-cites-other",     "reviewed T400 which landed SHA; my own work is on the branch", False),
    ("H-diverges-at",            "diverges from origin/main at commit SHA",              False),
    ("K-stack-region-base",      "stack SHA (T400 base) -> my work",                     False),
    ("L-supersedes",             "supersedes the work merged as SHA by T400",            False),
    ("I-genuine-landing",        "landed SHA on softhouse/TN-mine",                      True),
    ("P1-pipeline-MERGED-at",    "MERGED at SHA by fire 20260828-080001",                True),
    ("P2-pipeline-COMPLETE-at",  "COMPLETE @ SHA, scope clean",                          True),
    ("P3-tip",                   "tip SHA, 3 files",                                    True),
]
SHA = "a1b2c3d4"
print("%-26s %-8s %-8s %s" % ("case", "LANDING", "want", ""))
print("-" * 62)
bad = 0
for name, tmpl, want in CASES:
    note = tmpl.replace("SHA", SHA)
    t = {"id": "TN", "status": "done", "branch": "softhouse/TN-mine", "note": note}
    got = SHA in M.landing_shas(t, "TN")
    ok = got == want
    if not ok:
        bad += 1
    print("%-26s %-8s %-8s %s" % (name, got, want, "ok" if ok else "*** STILL BROKEN ***"))
    print("     %s" % note)
print("\n%d case(s) still wrong" % bad)
