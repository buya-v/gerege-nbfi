#!/usr/bin/env python3
"""T41 leak-grep: after every correction, grep the WHOLE document (and contract.go)
for restatements of the corrected claim.  Correction leak is this project's
signature failure and revision 7 itself shipped two leaks into its own pass 1.

Each pattern below is a phrase that would be STALE under revision 8.  A hit is
not automatically a defect -- the revision-history entries for revisions 1-7 are
HISTORY and correctly preserve what those revisions said -- so every hit is
printed with its line and judged by hand in the handoff.
"""
import io
import re

FILES = ["docs/adr/DEC-1-schedule-generator-adapter.md",
         "nexus/internal/apps/loanschedule/contract/contract.go"]

PATTERNS = [
    ("N-1  the two-argument framing",
     r"differ in TWO arguments|two argument differences exactly one is live|"
     r"inert inside the graded domain\b.*days-in-month|"
     r"second difference is inert inside the graded domain"),
    ("T39  periodRatio ungraded / corpus blind to it",
     r"MULTIPLIER rule remains? (specified-from-source and )?ungraded|"
     r"NO CAPTURE CAN DETECT IT|periodRatio.*NOT OBSERVED|"
     r"item 3e has no capture|only one of the six with no capture"),
    ("T39  the binding is six vectors",
     r"binding is six vectors|widen(s|ed) to six vectors|to six vectors|"
     r"from five vectors to six|all six\b|five of the six"),
    ("T40  three membership rules",
     r"THREE date-membership|three different membership|three membership rules|"
     r"all three of .4\.3\.2"),
    ("N-3  the ambient MathContext as the arithmetic",
     r"the `?MathContext`? actually in force|"
     r"tenant-global one \[`Money\.java:52`\]"),
    ("T40  Path-A charge power stated unscoped",
     r"the corpus has ZERO discriminating power over charges"),
    ("F-1  step B's k stated loosely",
     r"whole months from the seed to the repayment period's `FromDate` \(`ChronoUnit"),
]

for f in FILES:
    s = io.open(f, encoding="utf-8").read().split("\n")
    print("=" * 78)
    print(f)
    print("=" * 78)
    for label, pat in PATTERNS:
        hits = [(i + 1, ln) for i, ln in enumerate(s) if re.search(pat, ln)]
        print(f"  {label:<48} {len(hits)} hit(s)")
        for i, ln in hits:
            print(f"      line {i}: {ln.strip()[:150]}")
    print()
