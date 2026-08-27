#!/usr/bin/env python3
"""T251: which spans of DEC-2 does T247's revision-7 edit list never examine?

T247 reports 34 sites + a 16-entry HISTORY list. This script maps both onto the
document's own section structure and prints the spans that appear in NEITHER —
the population a 35th site can hide in. Enumeration, not sweeping (P-75).
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../../..")
ADR = os.path.join(ROOT, "docs/adr/DEC-2-gl-accounting-adapter.md")
LINES = open(ADR, encoding="utf-8").read().split("\n")
N = len(LINES)

# T247's 34 edit sites, as spans, transcribed from REVISION-7-PROPOSED.md §A.1-A.3.
EDIT_SPANS = [(3, 73), (75, 77), (80, 88), (90, 96), (247, 253), (458, 461),
              (708, 711), (813, 815), (819, 819), (820, 820), (825, 825),
              (827, 830), (1304, 1311), (1449, 1452), (1504, 1504), (1626, 1626),
              (2021, 2024), (2044, 2048), (2345, 2409), (2411, 2437)]

# T247's §A.4 HISTORY enumeration, verbatim.
HISTORY_SPANS = [(19, 36), (134, 134), (1360, 1368), (1612, 1626), (1720, 1720),
                 (1795, 1795), (1852, 1852), (1928, 1993), (2426, 2430),
                 (2614, 2615), (2681, 2682), (2841, 2860), (2865, 2865),
                 (2883, 2995), (3017, 3017), (3034, 3034)]


def covered(n):
    for a, b in EDIT_SPANS + HISTORY_SPANS:
        if a <= n <= b:
            return True
    return False


HEAD = re.compile(r"^#{1,4}\s+(.*)$")


def sections():
    out = []
    for n, l in enumerate(LINES, 1):
        m = HEAD.match(l)
        if m:
            out.append((n, m.group(1)))
    out.append((N + 1, "<EOF>"))
    return out


# Present-tense claims that the ledger is ungraded / has no vectors / nothing
# is expressible. Calibrated below.
CLAIM = re.compile(
    r"(?i)(grades?\s+(nothing|none|no\b)"
    r"|nothing\s+grades"
    r"|(no|zero)\s+`?ledger`?\s+vectors?"
    r"|not\s+(yet\s+)?(built|graded|gradeable)"
    r"|is\s+not\s+built"
    r"|ungraded\s+today"
    r"|no\s+such\s+PASS"
    r"|cannot\s+(currently\s+)?be\s+(written|graded))")


def calibrate():
    """POSITIVE: L828 (a site T247 itself classifies FALSE) must match.
    NEGATIVE: L817, the table header, must NOT match — and it is not a
    substring of the positive, so the two genuinely discriminate."""
    pos = bool(CLAIM.search(LINES[828 - 1]))
    neg = bool(CLAIM.search(LINES[817 - 1]))
    print("CALIBRATION")
    print("  POSITIVE L828 -> %s" % ("match (correct)" if pos else "MISS (VOID)"))
    print("  NEGATIVE L817 -> %s" % ("no match (correct)" if not neg else "MATCH (VOID)"))
    return pos and not neg


def main():
    if not calibrate():
        print("CALIBRATION FAIL — results void.")
        return 2
    secs = sections()
    print("\n=== CLAIM-SHAPED LINES IN SPANS T247's LIST NEVER EXAMINES ===")
    print("(neither an edit site nor on the HISTORY list)\n")
    hits = 0
    for n in range(1, N + 1):
        if covered(n):
            continue
        if CLAIM.search(LINES[n - 1]):
            sec = "?"
            for (sn, title), (nn, _) in zip(secs, secs[1:]):
                if sn <= n < nn:
                    sec = "L%d %s" % (sn, title[:60])
                    break
            hits += 1
            print("  L%-5d [%s]\n        %s\n" % (n, sec, LINES[n - 1].strip()[:200]))
    print("TOTAL uncovered claim-shaped lines: %d" % hits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
