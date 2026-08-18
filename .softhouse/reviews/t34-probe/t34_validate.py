"""
T34 (A): can DEC-1 revision 6, transcribed from its TEXT ALONE, reproduce the
thirteen committed observations?

The thirteen expectations below are QUOTED from the committed capture and probe
files (.softhouse/capture/out/capture-prod-raw.json and
.softhouse/reviews/t23-probe/*), exactly as .softhouse/reviews/t33-probe/
t33_spec_check.py quotes them.  They are transcriptions of already-committed
observations; this task took NO oracle observation of its own.
"""
from datetime import date
from decimal import Decimal
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t34_model import Request, generate, totals, m2s

# (principal MAJOR units, n, rate %, disbursement date or None (== schedule start),
#  (level installment, final installment, total interest), provenance)
CASES = [
    (100,      6,  "7.0",  None, ("17.01", "17.00", "2.05"),
     "shipped fixture / capture-prod-raw.json P-00"),
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


def run():
    bad = 0
    print("(A) DEC-1 revision 6, transcribed from the TEXT ALONE, vs the 13")
    print("    COMMITTED observations.  Nothing here is a new observation.")
    print()
    print(f"{'principal':>12} {'n':>3} {'rate':>5} {'disb':>11} "
          f"{'level':>14} {'final':>14} {'tot int':>14}  ok")
    for p, n, r, disb, expect, prov in CASES:
        start = date(2024, 1, 1)
        req = Request(start=start, disb=disb or start,
                      principal_minor=p * 100, n=n, rate_pct=Decimal(r))
        rows = generate(req)
        rel = [x for x in rows if x.emi_minor != 0]
        level = rel[0].emi_minor
        final = rows[-1].emi_minor
        _, ti, _ = totals(rows)
        got = (m2s(level), m2s(final), m2s(ti))
        ok = got == expect
        if not ok:
            bad += 1
        print(f"{p:>12} {n:>3} {r:>5} {str(disb or ''):>11} "
              f"{got[0]:>14} {got[1]:>14} {got[2]:>14}  {'OK' if ok else 'MISMATCH'}")
        if not ok:
            print(f"{'':>12} {'':>3} {'':>5} {'expected':>11} "
                  f"{expect[0]:>14} {expect[1]:>14} {expect[2]:>14}   [{prov}]")
    print()
    print(f"reproduced {len(CASES) - bad} of {len(CASES)}")
    return bad


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
