#!/usr/bin/env python3
"""T32 -- run the independent from-text transcription (t32_model.py) against the
THIRTEEN OBSERVATIONS ALREADY COMMITTED under .softhouse/reviews/t23-probe/.

NO LIVE ORACLE WAS CONTACTED.  The expectations below are re-used verbatim from
.softhouse/reviews/t29-probe/t29_validate.py, which quotes them from the
committed capture files; the MODEL is this task's own and shares no code with
t29_rederive.py or t31_spec_check.py.
"""
from datetime import date
from t32_model import generate, summarise

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


def run(days_reading, interest_reading, label):
    ok = bad = 0
    print(f"--- {label}  (days_reading={days_reading}, interest={interest_reading})")
    for p, n, r, disb, expect, prov in CASES:
        got = summarise(generate(p, n, r, disb=disb,
                                 days_reading=days_reading,
                                 interest_reading=interest_reading))
        good = got == expect
        ok, bad = ok + good, bad + (not good)
        print(f"  {'PASS' if good else 'FAIL'}  P={p:<9} n={n:<3} {r:>5}%"
              f"{('  disb=' + str(disb)) if disb else '':<20}  {got}")
        if not good:
            print(f"        expected {expect}   [{prov}]")
    print(f"  => {ok} pass, {bad} fail, out of {len(CASES)}\n")
    return ok, bad


if __name__ == "__main__":
    print("T32 -- independent from-text transcription vs COMMITTED observations")
    print("(no live oracle contacted; expectations quoted, never re-taken)\n")
    run("source", "spec", "DEC-1 rev 5 as transcribed")
    run("text", "spec", "control A: the ratio-is-always-1 reading of 4.1/contract.go")
    run("source", "textbook", "control B: the textbook balance * rateFactor reading")
