#!/usr/bin/env python3
"""T29 -- validate `t29_rederive` against observations ALREADY COMMITTED under
`.softhouse/reviews/t23-probe/`.  NO LIVE ORACLE WAS CONTACTED; every expected
value below is quoted from a committed capture file, never re-taken."""

from datetime import date
from t29_rederive import generate, f

# (principal, n, rate, disbursement offset, expected first/last/totalInterest,
#  provenance)
CASES = [
    (100,      6,  "7.0",  None, ("17.01", "17.00", "2.05"),
     "shipped fixture / DEC-1 4.3 observed (-0.01 residual)"),
    (1014632,  6,  "7.0",  None, ("172574.64", "172574.62", "20815.82"),
     "t23-probe2-output.txt CASE P=1014632"),
    (127704,  36, "16.8",  None, ("4540.30", "4540.06", "35746.56"),
     "t23-probe2-output.txt CASE P=127704"),
    (135623,   6,  "7.0",  None, ("23067.56", "23067.59", "2782.39"),
     "t23-probe2-output.txt CASE P=135623"),
    (2345024,  6,  "7.0",  None, ("398855.60", "398855.63", "48109.63"),
     "t23-probe2-output.txt CASE P=2345024"),
    (167299,   6, "21.6",  None, ("29665.91", "29665.94", "10696.49"),
     "t23-probe2-output.txt CASE P=167299"),
    (64352,   12, "21.6",  None, ("6010.61", "6010.55", "7775.26"),
     "t23-probe2-output.txt CASE P=64352"),
    (1000,    18, "18.5",  None, ("64.04", "64.14", "152.82"),
     "t23-probe2-output.txt CASE P=1000"),
    (246489,  18, "18.5",  None, ("15786.24", "15786.14", "37663.22"),
     "t23-probe2-output.txt CASE P=246489"),
    (16838,   36, "16.8",  None, ("598.65", "598.46", "4713.21"),
     "t23-probe2-output.txt CASE P=16838"),
    (40595,   36, "16.8",  None, ("1443.28", "1443.47", "11363.27"),
     "t23-probe2-output.txt CASE P=40595"),
    (1200000,  6, "21.6",  None, ("212787.28", "212787.30", "76723.70"),
     "t23-probe-output.txt Q0a"),
    (1200000,  6, "21.6", date(2024, 2, 1), ("253114.12", "253114.10", "65570.58"),
     "t23-probe-output.txt Q0b -- disbursement ON repayment 1's due date"),
]

if __name__ == "__main__":
    print("T29 validation of the source-faithful model against COMMITTED observations")
    print("(no live oracle was contacted; expectations are quoted, not re-taken)\n")
    ok = bad = 0
    for p, n, r, disb, expect, prov in CASES:
        rows = generate(p, n, r, disb=disb, model="source")
        rel = [x for x in rows if x["emi"] != 0]
        got = (f(rel[0]["emi"]), f(rows[-1]["emi"]),
               f(sum(x["interest"] for x in rows)))
        good = got == expect
        ok, bad = ok + good, bad + (not good)
        print(f"  {'PASS' if good else 'FAIL'}  P={p:<9} n={n:<3} {r:>5}%"
              f"{'  disb=' + str(disb) if disb else '':<20}"
              f"  level/final/interest = {got}")
        if not good:
            print(f"        expected {expect}   [{prov}]")
    print(f"\n  {ok} pass, {bad} fail, out of {len(CASES)}")
