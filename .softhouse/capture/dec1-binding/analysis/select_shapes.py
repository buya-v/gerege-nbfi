#!/usr/bin/env python3
"""T37 step 1 -- SHAPE SELECTION, run BEFORE any capture.

For each candidate shape, run DEC-1 revision 6's reading and the WRONG reading the
corresponding binding item exists to separate, and report whether they differ.  A
shape both readings reproduce is not worth a capture: the observation could not
discriminate anything.

*** THIS IS A RE-DERIVATION, NOT AN OBSERVATION.  NO ORACLE IS CONTACTED HERE. ***
The figures printed are candidate-shape predictions only.  They exist to choose
what to capture; the capture is the evidence, and ../out/ holds it.
"""
from datetime import date

import dec1_readings as m

D = date

# (item, label, wrong-reading kwargs, [ (principal, n, rate, start, disb) ... ])
CANDIDATES = [
    ("3", "EMI re-adjust loop ABSENT (a port that never implements it)",
     {"loop_reading": "absent"},
     [(1014632, 6, "7.0", D(2024, 1, 1), None),
      (127704, 36, "16.8", D(2024, 1, 1), None),
      (100025, 12, "16.8", D(2024, 1, 1), None),
      (1200000, 6, "21.6", D(2024, 1, 1), None)]),

    ("3a", "loop present but WITHOUT the strict adoption test (step 7 omitted)",
     {"loop_reading": "no_adoption"},
     [(100025, 12, "16.8", D(2024, 1, 1), None),
      (1014632, 6, "7.0", D(2024, 1, 1), None),
      (127704, 36, "16.8", D(2024, 1, 1), None)]),

    ("3b", "textbook `balance x rateFactor` interest (round-trip collapsed)",
     {"interest_reading": "textbook"},
     [(13202, 6, "16.8", D(2024, 1, 1), None),
      (3924149, 6, "16.8", D(2024, 1, 31), None),
      (1814727, 6, "21.6", D(2024, 1, 31), None)]),

    ("3c", "n = NumberOfRepayments instead of |relatedRepaymentPeriods|",
     {"n_reading": "numberofrepayments"},
     [(10548069, 6, "16.8", D(2024, 1, 1), D(2024, 2, 1)),
      (1222552, 6, "18.5", D(2024, 1, 1), D(2024, 2, 1)),
      (13549647, 6, "21.6", D(2024, 1, 1), D(2024, 2, 1))]),

    ("3d", "day-count ratio hard-coded to 1 (no actual/calculated proration)",
     {"day_counts": "ratio1"},
     [(1200000, 6, "21.6", D(2024, 1, 1), D(2024, 1, 15)),
      (127704, 36, "16.8", D(2024, 1, 1), D(2024, 1, 20)),
      (50000000, 12, "18.5", D(2024, 1, 1), D(2024, 1, 2))]),
]


def diff_rows(a, b):
    """Count differing per-period cells + differing totals."""
    n = 0
    if a["totalInterestAmount"] != b["totalInterestAmount"]:
        n += 1
    if a["totalRepaymentAmount"] != b["totalRepaymentAmount"]:
        n += 1
    for pa, pb in zip(a["periods"], b["periods"]):
        for k in ("principal", "interest", "total", "balance"):
            n += (pa[k] != pb[k])
    return n


def main():
    print("T37 SHAPE SELECTION -- re-derivation only, NO ORACLE CONTACTED.")
    print("Every figure below is a prediction used to choose what to capture.\n")
    for item, label, kw, shapes in CANDIDATES:
        print(f"=== DEC-1 section 8 item {item} -- wrong reading: {label}")
        for p, n, r, start, disb in shapes:
            spec = m.reading(p, n, r, start, disb)
            wrong = m.reading(p, n, r, start, disb, **kw)
            d = diff_rows(spec, wrong)
            tag = "SEPARATES" if d else "identical "
            ds = f" disb={disb}" if disb else ""
            print(f"  {tag}  MNT {p:>10,} / {n:<3} x {r:>5}%  start={start}{ds}"
                  f"   differing cells={d}")
            print(f"             revision 6 total interest = {spec['totalInterestAmount']:>15}"
                  f"   final installment = {spec['periods'][-1]['total']:>14}")
            print(f"             wrong reading            = {wrong['totalInterestAmount']:>15}"
                  f"                       = {wrong['periods'][-1]['total']:>14}")
        print()


if __name__ == "__main__":
    main()
