"""
T39 -- CONTROLS.  The checks that license everything else.

  C1  CALIBRATION.  T39-CAL against the SHIPPED Fineract test literal, at the
      MathContext that literal was produced under -- (12, HALF_UP)
      [EmbeddableProgressiveLoanScheduleGeneratorTest.java:44].  Labelled as a
      calibration; it is NEVER a parity vector, because 12 is not the production
      precision (MoneyHelper.PRECISION = 19).

  C2  REPRODUCTION.  T39-CTL-Q0a against committed observation Q0a
      (.softhouse/reviews/t23-probe/t23-probe-output.txt:5-16), taken by a different
      harness on a different task.

  C3  REPRODUCTION.  T39-CTL-1 against committed capture T37-3-A as published in
      .softhouse/handoff/T37-dec1-binding-captures.md.

  C4  REPRODUCTION.  T39-ME-A against committed capture T37-3b-2 as published in
      .softhouse/handoff/T37-dec1-binding-captures.md.

Every expectation below is TRANSCRIBED from a committed record or a source literal,
with the file and line beside it.  NOTHING here is computed, extrapolated or
interpolated -- a plausible invented number looks exactly like a real one.

Exact decimal strings only.  No float.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOAD = os.path.join(HERE, "..", "out", "t39-periodratio.json")

# ---------------------------------------------------------------------------
# C1 -- transcribed from
# fineract-progressive-loan-embeddable-schedule-generator/src/test/java/org/apache/
#   fineract/portfolio/loanaccount/loanschedule/domain/
#   EmbeddableProgressiveLoanScheduleGeneratorTest.java
# MathContext at :44 ; assertions at :74-77 ; rows at :79-95.
# The test writes its literals as Java doubles; they are transcribed here as the
# exact decimal strings the seam renders with BigDecimal.toPlainString().
# ---------------------------------------------------------------------------
C1_TOTALS = {                                  # :74-77
    "loanTermInDays": "182",
    "totalDisbursedAmount": "100.00",
    "totalInterestAmount": "2.05",
    "totalRepaymentAmount": "102.05",
}
C1_DISB = {"fromDate": "2024-01-01", "dueDate": "2024-01-01", "principal": "100.00"}  # :80
C1_ROWS = [                                    # :81-95, (from, due, principal, interest,
                                               #          fee, penalty, total, balance,
                                               #          totalOutstandingBalance)
    ("2024-01-01", "2024-02-01", "16.43", "0.58", "0.00", "0.00", "17.01", "83.57", "85.04"),
    ("2024-02-01", "2024-03-01", "16.52", "0.49", "0.00", "0.00", "17.01", "67.05", "68.03"),
    ("2024-03-01", "2024-04-01", "16.62", "0.39", "0.00", "0.00", "17.01", "50.43", "51.02"),
    ("2024-04-01", "2024-05-01", "16.72", "0.29", "0.00", "0.00", "17.01", "33.71", "34.01"),
    ("2024-05-01", "2024-06-01", "16.81", "0.20", "0.00", "0.00", "17.01", "16.90", "17.00"),
    ("2024-06-01", "2024-07-01", "16.90", "0.10", "0.00", "0.00", "17.00", "0.00", "0.00"),
]

# ---------------------------------------------------------------------------
# C2 -- transcribed from .softhouse/reviews/t23-probe/t23-probe-output.txt:5-16
# (from, due, principal, interest, total, balance).  That record does not carry
# fee, penalty or totalOutstandingBalance, so those three columns are not part of
# this control and are not asserted here.
# ---------------------------------------------------------------------------
C2_TOTALS = {"loanTermInDays": "182", "totalDisbursedAmount": "1200000.00",
             "totalInterestAmount": "76723.70", "totalRepaymentAmount": "1276723.70"}
C2_DISB = {"dueDate": "2024-01-01", "principal": "1200000.00"}
C2_ROWS = [
    ("2024-01-01", "2024-02-01", "191187.28", "21600.00", "212787.28", "1008812.72"),
    ("2024-02-01", "2024-03-01", "194628.65", "18158.63", "212787.28", "814184.07"),
    ("2024-03-01", "2024-04-01", "198131.97", "14655.31", "212787.28", "616052.10"),
    ("2024-04-01", "2024-05-01", "201698.34", "11088.94", "212787.28", "414353.76"),
    ("2024-05-01", "2024-06-01", "205328.91", "7458.37", "212787.28", "209024.85"),
    ("2024-06-01", "2024-07-01", "209024.85", "3762.45", "212787.30", "0.00"),
]

# ---------------------------------------------------------------------------
# C3 -- transcribed from .softhouse/handoff/T37-dec1-binding-captures.md, the
# "Item 3 -- T37-3-A" table (window, principal, interest, total, balance) and its
# totals line.
# ---------------------------------------------------------------------------
C3_TOTALS = {"loanTermInDays": "182", "totalDisbursedAmount": "1014632.00",
             "totalInterestAmount": "20815.82", "totalRepaymentAmount": "1035447.82"}
C3_ROWS = [
    ("2024-01-01", "2024-02-01", "166655.95", "5918.69", "172574.64", "847976.05"),
    ("2024-02-01", "2024-03-01", "167628.11", "4946.53", "172574.64", "680347.94"),
    ("2024-03-01", "2024-04-01", "168605.94", "3968.70", "172574.64", "511742.00"),
    ("2024-04-01", "2024-05-01", "169589.48", "2985.16", "172574.64", "342152.52"),
    ("2024-05-01", "2024-06-01", "170578.75", "1995.89", "172574.64", "171573.77"),
    ("2024-06-01", "2024-07-01", "171573.77", "1000.85", "172574.62", "0.00"),
]

# ---------------------------------------------------------------------------
# C4 -- transcribed from .softhouse/handoff/T37-dec1-binding-captures.md, item 3b:
# "T37-3b-2 -- MNT 3,924,149 / 6 x 16.8 %, start = disbursement 2024-01-31 ...
#  totalInterest 194,510.78, level 686,443.30, final 686,443.28".
# The handoff publishes those three scalars only for this shape, so the control is
# three scalars wide and says so.
# ---------------------------------------------------------------------------
C4 = {"totalInterestAmount": "194510.78", "level": "686443.30", "final": "686443.28"}


def cap(doc, cid):
    for c in doc["captures"]:
        if c["id"] == cid:
            return c
    raise KeyError(cid)


def repayments(c):
    return [p for p in c["observed"]["periods"] if p["type"] == "REPAYMENT"]


def disbursement(c):
    for p in c["observed"]["periods"]:
        if p["type"] == "DISBURSEMENT":
            return p
    raise KeyError("no disbursement row")


def check(name, expected, actual, bad):
    if expected != actual:
        bad.append(f"{name}: expected {expected!r}, observed {actual!r}")


def main() -> int:
    doc = json.load(open(PAYLOAD))
    bad: list[str] = []
    print("T39 controls -- expectations TRANSCRIBED from committed records / source literals.\n")

    # ---- C1 ---------------------------------------------------------------
    c = cap(doc, "T39-CAL")
    print("C1 CALIBRATION  T39-CAL vs the shipped test literal at (12, HALF_UP)"
          "  [EmbeddableProgressiveLoanScheduleGeneratorTest.java:44,74-95]")
    assert c["inputs"]["mathContextPrecision"] == 12
    o = c["observed"]
    check("C1 loanTermInDays", C1_TOTALS["loanTermInDays"], str(o["loanTermInDays"]), bad)
    for k in ("totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"):
        check("C1 " + k, C1_TOTALS[k], o[k], bad)
    d = disbursement(c)
    for k, v in C1_DISB.items():
        check("C1 disbursement." + k, v, d[k], bad)
    rows = repayments(c)
    check("C1 repayment row count", str(len(C1_ROWS)), str(len(rows)), bad)
    for i, (frm, due, pr, it, fe, pe, tt, ba, tob) in enumerate(C1_ROWS, start=1):
        r = rows[i - 1]
        for col, exp in (("fromDate", frm), ("dueDate", due), ("principal", pr),
                         ("interest", it), ("fee", fe), ("penalty", pe), ("total", tt),
                         ("balance", ba), ("totalOutstandingBalance", tob)):
            check(f"C1 period[{i}].{col}", exp, r[col], bad)
    print("   -> compared 4 totals + 3 disbursement columns + 6 rows x 9 columns = 61 cells\n")

    # ---- C2 ---------------------------------------------------------------
    c = cap(doc, "T39-CTL-Q0a")
    print("C2 REPRODUCTION  T39-CTL-Q0a vs committed observation Q0a"
          "  [.softhouse/reviews/t23-probe/t23-probe-output.txt:5-16]")
    o = c["observed"]
    check("C2 loanTermInDays", C2_TOTALS["loanTermInDays"], str(o["loanTermInDays"]), bad)
    for k in ("totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"):
        check("C2 " + k, C2_TOTALS[k], o[k], bad)
    d = disbursement(c)
    for k, v in C2_DISB.items():
        check("C2 disbursement." + k, v, d[k], bad)
    rows = repayments(c)
    check("C2 repayment row count", str(len(C2_ROWS)), str(len(rows)), bad)
    for i, (frm, due, pr, it, tt, ba) in enumerate(C2_ROWS, start=1):
        r = rows[i - 1]
        for col, exp in (("fromDate", frm), ("dueDate", due), ("principal", pr),
                         ("interest", it), ("total", tt), ("balance", ba)):
            check(f"C2 period[{i}].{col}", exp, r[col], bad)
    print("   -> compared 4 totals + 2 disbursement columns + 6 rows x 6 columns = 42 cells")
    print("      (that record carries no fee / penalty / totalOutstandingBalance column)\n")

    # ---- C3 ---------------------------------------------------------------
    c = cap(doc, "T39-CTL-1")
    print("C3 REPRODUCTION  T39-CTL-1 vs committed capture T37-3-A"
          "  [.softhouse/handoff/T37-dec1-binding-captures.md, item 3]")
    o = c["observed"]
    check("C3 loanTermInDays", C3_TOTALS["loanTermInDays"], str(o["loanTermInDays"]), bad)
    for k in ("totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"):
        check("C3 " + k, C3_TOTALS[k], o[k], bad)
    rows = repayments(c)
    check("C3 repayment row count", str(len(C3_ROWS)), str(len(rows)), bad)
    for i, (frm, due, pr, it, tt, ba) in enumerate(C3_ROWS, start=1):
        r = rows[i - 1]
        for col, exp in (("fromDate", frm), ("dueDate", due), ("principal", pr),
                         ("interest", it), ("total", tt), ("balance", ba)):
            check(f"C3 period[{i}].{col}", exp, r[col], bad)
    print("   -> compared 4 totals + 6 rows x 6 columns = 40 cells\n")

    # ---- C4 ---------------------------------------------------------------
    c = cap(doc, "T39-ME-A")
    print("C4 REPRODUCTION  T39-ME-A vs committed capture T37-3b-2"
          "  [.softhouse/handoff/T37-dec1-binding-captures.md, item 3b]")
    o = c["observed"]
    rows = repayments(c)
    check("C4 totalInterestAmount", C4["totalInterestAmount"], o["totalInterestAmount"], bad)
    check("C4 level installment", C4["level"], rows[0]["total"], bad)
    check("C4 final installment", C4["final"], rows[-1]["total"], bad)
    print("   -> compared the 3 scalars the handoff publishes for this shape\n")

    if bad:
        for b in bad:
            print("FAIL: " + b)
        print(f"\nCONTROLS FAILED: {len(bad)} mismatches.  Nothing in this capture is admissible.")
        return 1
    print("ALL FOUR CONTROLS PASS -- every transcribed expectation reproduced digit for digit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
