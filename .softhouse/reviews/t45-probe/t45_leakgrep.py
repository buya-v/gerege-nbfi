#!/usr/bin/env python3
"""T45 - correction-leak grep.

Correction leak is this project's signature failure: a correction is applied where the
reviewer pointed and left standing in the four other places the document restates it.
It bit revisions 7 and 8 in their own second passes, and P1-T43-1 IS a leak -- one wrong
citation repeated four times.

So: for every correction revision 9 makes, grep the WHOLE document (and contract.go) for
the pattern the correction retires, and require every remaining hit to be an explicit
"revision 8 said X, revision 9 corrects it" acknowledgement rather than a live restatement.
"""
import re
import sys

TARGETS = [
    "docs/adr/DEC-1-schedule-generator-adapter.md",
    "nexus/internal/apps/loanschedule/contract/contract.go",
]

# (label, retired-pattern, marker that makes a hit an ACKNOWLEDGEMENT rather than a leak)
CHECKS = [
    ("P1-T43-1  :504 cited as a cumulative DIFFERENCE",
     r"AbstractCumulativeLoanScheduleGenerator\.java:504",
     r"(?i)(share|byte-identical|is not a difference|same separated-path line|revision 8 cited|md5|ProgressiveLoanScheduleGenerator\.java:486)"),
    ("P1-T43-1  the cumulative generator 'adds them / does the opposite'",
     r"cumulative generator (does the opposite|adds them|does add them)",
     r"(?!)"),          # any hit at all is a leak
    ("P1-T43-3  M4 stated as deciding where a CHARGE lands, unqualified",
     r"which (repayment )?row a \*?\*?CHARGE\*?\*? lands on",
     r"(isDue|SPECIFIED_DUE_DATE|for the three|M5|only)"),
    ("P1-T43-3  'the FOUR date-membership rules'",
     r"FOUR date-membership rules|four different\*?\*? date-membership|all four\*?\*? of §4\.3\.2",
     r"(?!)"),
    ("P1-T43-2  'reached at exactly these call sites'",
     r"reached at exactly these call sites",
     r"(?!)"),
    ("P1-T43-2  'every remaining site ... which the graded domain excludes'",
     r"[Ee]very remaining site sits on the installment-multiple",
     r"(revision 8 closed|was \*\*false)"),
    ("P1-T43-2  the four-site tenant-global list Money.java:103, :115, :160, :377",
     r"Money\.java:103`?, `?:115`?, `?:160`?,? ?`?:169`?,? ?`?:377",
     r"(eleven|:131|:233|:266)"),
    ("T44 F39-1  'separates / grades the month-end special case' unqualified",
     r"separating step B's month-end special case|separates §4\.1\.1 step B's \*\*month-end special case\*\*",
     r"(?!)"),
    ("T44 A-5  'no half-cent tie exists'",
     r"T40 proved none exists",
     r"(?!)"),
    ("P2-T43-2  a bare cell count with no leaf set",
     r"1,224 cells\)|1,239 cells of all 15 parity-setting captures\*\* with zero mismatches\.",
     r"(?!)"),
    ("P2-T43-1  C-1's three-term progressive semantics, missing the down payment",
     r"disbursement charges \+ Σ\(principal \+ interest\) \+ separated",
     r"(?!)"),
]


def main():
    print("T45 CORRECTION-LEAK GREP over the whole document and contract.go")
    print()
    bad = 0
    for label, pat, ackpat in CHECKS:
        rx = re.compile(pat)
        ack = re.compile(ackpat)
        hits = []
        for t in TARGETS:
            lines = open(t).read().split("\n")
            for i, line in enumerate(lines, start=1):
                for m in rx.finditer(line):
                    # context window: +/- 260 chars within the line, PLUS the three lines
                    # either side, because these documents wrap a single argument over
                    # several short lines and a line-scoped window reports the correction
                    # itself as a leak.
                    lo = max(0, m.start() - 260)
                    ctx = "\n".join(lines[max(0, i - 4):i + 3])
                    shown = line[lo:m.end() + 260]
                    hits.append((t, i, bool(ack.search(ctx)), shown))
        leaks = [h for h in hits if not h[2]]
        status = "CLEAN" if not leaks else f"LEAK x{len(leaks)}"
        print(f"[{status:<8}] {label}")
        print(f"            hits: {len(hits)}   acknowledged: {len(hits) - len(leaks)}   live: {len(leaks)}")
        for t, i, _, ctx in leaks:
            print(f"            LIVE  {t}:{i}")
            print(f"                  ...{ctx}...")
        bad += len(leaks)
        print()
    print(f"TOTAL LIVE LEAKS: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
