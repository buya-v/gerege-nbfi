#!/usr/bin/env python3
"""T247 sweep instrument. Enumerates claim-family hits in DEC-2 by line number.

P-75: does not use `grep` or `rg` (shell functions / absent binary). Pure python `re`
over bytes read from the file, so there is no PATH, no --exclude-dir, no --ignore-files,
and no pipeline that can swallow an exit code.

Self-calibration is run FIRST and on BOTH polarities (known positive AND known negative);
if either arm misbehaves the script exits non-zero and prints nothing else.
"""
import re
import sys

PATH = "docs/adr/DEC-2-gl-accounting-adapter.md"

FAMILIES = {
    "F1 ledger-vector-existence": r"(?i)no `?ledger`? vector|zero `?ledger`? vectors?|ledger vector exists|holds `?loanschedule`?",
    "F2 expressibility": r"(?i)express(ible|ed|ion|es)",
    "F3 nothing-grades": r"(?i)nothing grades|grades none|no grading|ungraded|not graded|graded by nothing|graded today|checked by anything|currently checked",
    "F4 conformance-PASS": r"(?i)conformance PASS|no such PASS",
    "F5 A2-15": r"A2-15",
    "F6 ratification-status": r"(?i)NOT RATIFIED|G-11|revision 5\)|NOT RATIFIABLE|DRAFT \(",
    "F7 machinery-5.3": r"(?i)§5\.3|machinery",
    "F8 money-cells": r"(?i)money cell",
    "F9 ls-vectors": r"\.softhouse/vectors/",
}


def calibrate(text):
    ok = True
    # known POSITIVE: the document's own title line
    if not re.search(r"^# DEC-2 — GL / accounting adapter contract$", text, re.M):
        print("CALIBRATION FAIL: known positive not found", file=sys.stderr)
        ok = False
    # known NEGATIVE: a string engineered not to occur
    neg = "ZZQQ-T247-KNOWN-NEGATIVE-NEEDLE"
    if re.search(neg, text):
        print("CALIBRATION FAIL: known negative WAS found", file=sys.stderr)
        ok = False
    # fabrication control: git grep -E matched `bmainb` against \bmain\b (P-75).
    # Prove this instrument does NOT do that.
    if re.search(r"\bmain\b", "bmainb"):
        print("CALIBRATION FAIL: word-boundary fabricates", file=sys.stderr)
        ok = False
    if not re.search(r"\bmain\b", "on main today"):
        print("CALIBRATION FAIL: word-boundary misses a true hit", file=sys.stderr)
        ok = False
    return ok


def main():
    with open(PATH, encoding="utf-8") as fh:
        text = fh.read()
    if not calibrate(text):
        return 2
    print("CALIBRATION OK: positive found, negative absent, no fabrication, no miss")
    print("FILE %s  lines=%d" % (PATH, text.count("\n") + 1))
    lines = text.split("\n")
    for name, rx in FAMILIES.items():
        print("\n" + "=" * 8 + " " + name)
        hits = 0
        for i, line in enumerate(lines, 1):
            if re.search(rx, line):
                hits += 1
                print("%5d | %s" % (i, line[:260]))
        print("  -- %d line(s)" % hits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
