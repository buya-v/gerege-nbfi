#!/usr/bin/env python3
"""T251 independent site enumeration over DEC-2.

Method (P-75: python re, never bare grep / never rg):

ARM A — the "restates a banner fact WITHOUT its words" class. This is the class
that hid L820 from two prior passes. It cannot be found by wording, so it is
found by ENUMERATION of the population that can contain it: every cell of every
markdown table row, plus every short standalone line. Any cell that is a bare
verdict ("NO.", "N/A", "Same reason", "Unchanged") is a candidate, because its
truth is inherited from a neighbour rather than stated.

ARM B — concept sweep, for completeness only, never as the primary instrument.

Calibrated on a KNOWN POSITIVE (L820 "| **NO.** Same reason. |", which arm A
must find) and a KNOWN NEGATIVE that is NOT a substring of the positive
(L817, the table's own header row, which arm A must NOT flag).
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../../..")
ADR = os.path.join(ROOT, "docs/adr/DEC-2-gl-accounting-adapter.md")

LINES = open(ADR, encoding="utf-8").read().split("\n")

# A bare verdict: the cell asserts a grading outcome but carries no ground of
# its own. Deliberately anchored, so "NO." does not match "NOT APPLICABLE ...".
BARE_VERDICT = re.compile(
    r"^\s*(?:\*\*)?(?:NO|N/A|NONE|ZERO|SAME|UNCHANGED|IDEM|DITTO)\b[^|]{0,60}$",
    re.IGNORECASE)


def table_cells():
    """Yield (lineno, cell_index, cell_text) for every markdown table row."""
    for n, line in enumerate(LINES, 1):
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|") and s.count("|") >= 3):
            continue
        if re.fullmatch(r"\|[\s:|-]+\|", s):      # the ---|--- separator
            continue
        cells = [c.strip() for c in s[1:-1].split("|")]
        for i, c in enumerate(cells):
            yield n, i, c


def arm_a():
    hits = []
    for n, i, c in table_cells():
        if not c:
            continue
        if BARE_VERDICT.match(c):
            hits.append((n, i, c))
    return hits


CONCEPTS = {
    "no-vector-exists": r"(?i)(no|zero)\s+`?ledger`?\s+vectors?\s+(exist|is|are)",
    "not-expressible": r"(?i)not?\s+\w*\s*expressib",
    "grades-nothing": r"(?i)(grades?\s+(nothing|none|no)|nothing\s+grades|ungraded)",
    "guard-ordinal": r"(?i)(seven|seventh|eight|eighth|sixth)\s+guard|guard[^.\n]{0,30}(seventh|sixth)",
    "pass46-only": r"(?i)(only thing|PASS 46)",
    "not-ratified": r"(?i)(DRAFT|not (yet )?ratified|would (buy|be) )",
    "no-such-pass": r"(?i)no\s+(such\s+)?`?ledger`?\s*(conformance\s+)?PASS",
}


def arm_b():
    out = {}
    for name, pat in CONCEPTS.items():
        rx = re.compile(pat)
        out[name] = [(n, LINES[n - 1].strip()[:150])
                     for n in range(1, len(LINES) + 1) if rx.search(LINES[n - 1])]
    return out


def calibrate():
    """Positive AND negative, and they must DISCRIMINATE (not substrings)."""
    pos_line, neg_line = 820, 817
    pos = [h for h in arm_a() if h[0] == pos_line]
    neg = [h for h in arm_a() if h[0] == neg_line]
    ok = bool(pos) and not neg
    print("CALIBRATION arm A")
    print("  known POSITIVE L%d  %r -> %s" %
          (pos_line, LINES[pos_line - 1][-40:], "FLAGGED (correct)" if pos else "MISSED (VOID)"))
    print("  known NEGATIVE L%d  %r -> %s" %
          (neg_line, LINES[neg_line - 1][:40], "not flagged (correct)" if not neg else "FLAGGED (VOID)"))
    if not ok:
        print("  CALIBRATION FAIL — arm A results are void.")
    return ok


def main():
    print("DEC-2: %d lines" % len(LINES))
    if not calibrate():
        return 2
    print("\n=== ARM A — bare-verdict table cells (inherit their ground) ===")
    for n, i, c in arm_a():
        print("  L%-5d cell[%d]  %s" % (n, i, c[:110]))
    print("\n=== ARM B — concept sweep (secondary) ===")
    for name, hits in arm_b().items():
        print("\n-- %s (%d) --" % (name, len(hits)))
        for n, txt in hits:
            print("  L%-5d %s" % (n, txt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
