#!/usr/bin/env python3
"""T247 P-69 RE-MEASURE: assert every line number this task cites still holds.

Run this immediately before committing, and again by the driver immediately
before LANDING revision 7. If any row fails, the edit list is stale and must be
re-measured before it is applied. That is the whole lesson of G-14.

Each row is (line_number, substring_that_must_be_on_it). A substring, not a
regex, so there is no word-boundary fabrication class to worry about (P-75).
"""
import os
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../../..")
ADR = os.path.join(ROOT, "docs/adr/DEC-2-gl-accounting-adapter.md")
SH = os.path.join(ROOT, ".softhouse/conformance.sh")

ADR_ROWS = [
    # --- the eight sites T246 reported ---
    (3, "NOTHING GRADES THIS CONTEXT'S MONEY. NOTHING GRADES THIS CONTEXT AT ALL."),
    (7, "Not one of them is currently checked by anything."),
    (10, "**No `ledger` vector exists.**"),
    (87, "until then `A2-15` (promote GL vectors) stays blocked,"),
    (815, "no `ledger` vector of any shape is currently expressible"),
    (819, "no admissible vector can carry a money cell, or any `ledger` cell"),
    (825, "there is no `ledger` conformance PASS to say nothing with"),
    (2437, "Today there is no such PASS to misread."),
    # --- the nine T246 did not ---
    (12, "**No `ledger` vector is EXPRESSIBLE.** The store's only accepted schema is"),
    (38, "`run_guards` invokes **seven**"),
    (39, "guards, not five; the seventh is `guard_ledger_invariants`"),
    (54, 'The "PASS 46" everybody quotes is `loanschedule`'),
    (70, "advance: `conformance.sh`'s hard guards *do* walk `nexus/internal/apps/ledger/`."),
    (76, "no grading whatsoever"),
    (247, "contains exactly two context directories"),
    (250, "not one parity vector grades it"),
    (458, "Being statable is not being graded."),
    (711, "is expressible is a separate question, answered no in §5."),
    (820, "| **NO.** Same reason. |"),
    (828, "grades none of them today."),
    # --- further down ---
    (1304, "THE (b) COLUMN OF THIS TABLE CANNOT CURRENTLY BE WRITTEN DOWN."),
    (1309, "Every row of the (b) table is therefore ungraded today"),
    (1449, "holds **46 promoted parity vectors, all `loanschedule`**"),
    (1450, "**The `ledger` context has"),
    (1504, "### 5.1 No `ledger` vector is expressible against the frozen vector schema"),
    (1626, "**What is true.** §5.1's heading:"),
    (2023, "cannot promote a `ledger` vector until **all** of the following exist"),
    (2044, "**Nine open, one landed.**"),
    (2345, "### 8.1 NOTHING GRADES THE LEDGER"),
    (2359, "**Zero `ledger` vectors exist.**"),
    (2361, "**Zero `ledger` vectors are EXPRESSIBLE**"),
    (2407, "**Ratifying DEC-2 changes none of the four.**"),
    (2411, "### 8.2 If ratified"),
    (2415, "stays unusable until the §5.3 machinery lands"),
    (2421, "**Nine of the ten §5.3 preconditions remain"),
    (2423, '**"PASS 46" remains the'),
    (2424, "only thing anyone can say about the ledger"),
    (2432, "### 8.3 If ratified, these remain true and must not be misread"),
    (2611, "## 10. Revision history"),
    # --- sites that must be UNCHANGED, asserted so a careless edit is caught ---
    (80, "**Status: DRAFT (revision 5)"),
    (90, "**Revision 5 changes exactly two things and nothing else**"),
    (827, "**The rule this table encodes:**"),
]

SH_ROWS = [
    (1300, "guard_ledger_invariants() {"),
    (1474, "run_guards() {"),
    (1494, "guard_ledger_invariants             || failed=1"),
    (1495, "guard_no_fail_open_instruments      || failed=1"),
]


def check(path, rows, label):
    lines = open(path, encoding="utf-8").read().split("\n")
    bad = 0
    print("\n=== %s  (%s, %d lines) ===" % (label, os.path.relpath(path, ROOT), len(lines)))
    for n, needle in rows:
        if n > len(lines):
            print("  MOVED  L%-5d file has only %d lines" % (n, len(lines)))
            bad += 1
            continue
        if needle in lines[n - 1]:
            print("  ok     L%-5d %s" % (n, needle[:74]))
        else:
            bad += 1
            print("  MOVED  L%-5d expected %r" % (n, needle[:74]))
            print("         got      %r" % lines[n - 1][:100])
    return bad


def main():
    # NEGATIVE CONTROL: a row that MUST fail. If it passes, the checker is not
    # actually comparing anything and every "ok" above is worthless.
    neg = check(ADR, [(1, "ZZQQ-T247-THIS-MUST-NOT-MATCH")], "NEGATIVE CONTROL (expect 1 MOVED)")
    if neg != 1:
        print("\nCALIBRATION FAIL: the negative control did not fail. Results are void.")
        return 2
    bad = check(ADR, ADR_ROWS, "DEC-2 ADR")
    bad += check(SH, SH_ROWS, "conformance.sh")
    print("\n%s: %d row(s) MOVED out of %d checked" %
          ("STALE — RE-MEASURE BEFORE APPLYING" if bad else "ALL LINE NUMBERS HOLD",
           bad, len(ADR_ROWS) + len(SH_ROWS)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
