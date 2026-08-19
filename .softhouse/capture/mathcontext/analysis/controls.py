#!/usr/bin/env python3
"""T42 controls -- contacts no oracle.  EXITS 1 ON ANY MISMATCH.

Every expectation below is TRANSCRIBED with file:line, never computed here.  Three of the four
reproduce records taken by OTHER harnesses on OTHER tasks, so the harness is not the variable.

  C1  T42-CAL      the shipped Fineract test literal
                   fineract-progressive-loan-embeddable-schedule-generator/src/test/java/.../
                   EmbeddableProgressiveLoanScheduleGeneratorTest.java:44 (MathContext(12, HALF_UP)),
                   :74-77 (totals), :79-95 (rows).  61 cells.
  C2  T42-CTL-Q0a  committed observation Q0a,
                   .softhouse/reviews/t23-probe/t23-probe-output.txt, also reproduced by T37-CTL-Q0a
                   and T39-CTL-Q0a.
  C3  T42-CTL-1    committed capture T37-3-A / T39-CTL-1, .softhouse/handoff/T37-dec1-binding-captures.md
  C4  T42-CTL-P0A  committed capture T39-P0-A, .softhouse/handoff/T39-periodratio-observation.md section 2
  C5  T42-CTL-MEB  committed capture T39-ME-B, same handoff section 2

Exact string comparison.  No float anywhere -- the shipped literal's `2.05` etc. are transcribed
as the decimal STRINGS the oracle emits, not as Java doubles.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
import os
PAYLOAD = Path(os.environ.get("T42_CONTROLS_PAYLOAD",
                             HERE.parent / "out" / "t42-mathcontext.json"))

# ---- C1: the shipped test literal, transcribed ---------------------------------------------
# EmbeddableProgressiveLoanScheduleGeneratorTest.java:74-77 and :79-95.  The test asserts
# doubles; the oracle emits BigDecimals at currency scale 2, so `100.00` is transcribed "100.00",
# `2.05` as "2.05", `0.0` as "0.00", `16.43` as "16.43".  Dates are transcribed verbatim.
CAL = {
    "loanTermInDays": "182",
    "totalDisbursedAmount": "100.00",
    "totalInterestAmount": "2.05",
    "totalRepaymentAmount": "102.05",
    "periods": [
        # type, from, due, principal, interest, fee, penalty, total, balance, totalOutstandingBalance
        ("DISBURSEMENT", "2024-01-01", "2024-01-01", "100.00", None, None, None, None, None, None),
        ("REPAYMENT", "2024-01-01", "2024-02-01", "16.43", "0.58", "0.00", "0.00", "17.01", "83.57", "85.04"),
        ("REPAYMENT", "2024-02-01", "2024-03-01", "16.52", "0.49", "0.00", "0.00", "17.01", "67.05", "68.03"),
        ("REPAYMENT", "2024-03-01", "2024-04-01", "16.62", "0.39", "0.00", "0.00", "17.01", "50.43", "51.02"),
        ("REPAYMENT", "2024-04-01", "2024-05-01", "16.72", "0.29", "0.00", "0.00", "17.01", "33.71", "34.01"),
        ("REPAYMENT", "2024-05-01", "2024-06-01", "16.81", "0.20", "0.00", "0.00", "17.01", "16.90", "17.00"),
        ("REPAYMENT", "2024-06-01", "2024-07-01", "16.90", "0.10", "0.00", "0.00", "17.00", "0.00", "0.00"),
    ],
}

# ---- C2..C5: committed observations, transcribed --------------------------------------------
# Only the values the committed artefacts actually publish are asserted.
COMMITTED = {
    # T39 handoff section 2, capture T39-CTL-Q0a; also committed observation Q0a
    "T42-CTL-Q0a": {"loanTermInDays": "182", "totalDisbursedAmount": "1200000.00",
                    "totalInterestAmount": "76723.70", "totalRepaymentAmount": "1276723.70"},
    # T39 handoff section 2, capture T39-CTL-1 == T37 item 3 capture T37-3-A
    "T42-CTL-1": {"totalDisbursedAmount": "1014632.00", "totalInterestAmount": "20815.82",
                  "totalRepaymentAmount": "1035447.82"},
    # T39 handoff section 2 worked example, capture T39-P0-A: term 185, total interest 76,984.00
    "T42-CTL-P0A": {"loanTermInDays": "185", "totalDisbursedAmount": "1200000.00",
                    "totalInterestAmount": "76984.00", "totalRepaymentAmount": "1276984.00"},
    # T39 handoff section 2 worked example, capture T39-ME-B
    "T42-CTL-MEB": {"totalDisbursedAmount": "1200000.00", "totalInterestAmount": "76723.70",
                    "totalRepaymentAmount": "1276723.70"},
}

# T39-P0-A's full period table, transcribed from the T39 handoff section 2 worked example.
# from, due, principal, interest, fee, penalty, balance, total, totalOutstandingBalance
P0A_ROWS = [
    ("2024-01-28", "2024-02-29", "192580.67", "20250.00", "0.00", "0.00", "1007419.33", "212830.67", "1064153.33"),
    ("2024-02-29", "2024-03-31", "193527.22", "19303.45", "0.00", "0.00", "813892.11", "212830.67", "851322.66"),
    ("2024-03-31", "2024-04-30", "198180.61", "14650.06", "0.00", "0.00", "615711.50", "212830.67", "638491.99"),
    ("2024-04-30", "2024-05-31", "201390.35", "11440.32", "0.00", "0.00", "414321.15", "212830.67", "425661.32"),
    ("2024-05-31", "2024-06-30", "205372.89", "7457.78", "0.00", "0.00", "208948.26", "212830.67", "212830.65"),
    ("2024-06-30", "2024-07-31", "208948.26", "3882.39", "0.00", "0.00", "0.00", "212830.65", "0.00"),
]

# T39-ME-B's full period table, transcribed from the same worked example (no fee/penalty column
# is published there, so those two are not asserted for this control).
MEB_ROWS = [
    ("2024-01-31", "2024-02-29", "191187.28", "21600.00", "1008812.72", "212787.28"),
    ("2024-02-29", "2024-03-31", "194628.65", "18158.63", "814184.07", "212787.28"),
    ("2024-03-31", "2024-04-30", "198131.97", "14655.31", "616052.10", "212787.28"),
    ("2024-04-30", "2024-05-31", "201698.34", "11088.94", "414353.76", "212787.28"),
    ("2024-05-31", "2024-06-30", "205328.91", "7458.37", "209024.85", "212787.28"),
    ("2024-06-30", "2024-07-31", "209024.85", "3762.45", "0.00", "212787.30"),
]


def main():
    doc = json.load(open(PAYLOAD))
    caps = {c["id"]: c for c in doc["captures"]}
    bad = []
    checked = 0

    def eq(where, expected, actual):
        nonlocal checked
        checked += 1
        if expected != actual:
            bad.append(f"{where}: expected {expected!r}, observed {actual!r}")

    # ---- C1 -------------------------------------------------------------------------------
    cal = caps["T42-CAL"]["observed"]
    eq("C1 T42-CAL.loanTermInDays", CAL["loanTermInDays"], str(cal["loanTermInDays"]))
    for k in ("totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"):
        eq(f"C1 T42-CAL.{k}", CAL[k], cal[k])
    if len(cal["periods"]) != len(CAL["periods"]):
        bad.append(f"C1 T42-CAL: {len(cal['periods'])} periods, expected {len(CAL['periods'])}")
    else:
        for i, (exp, got) in enumerate(zip(CAL["periods"], cal["periods"])):
            typ, frm, due, prin, inter, fee, pen, tot, bal, tob = exp
            eq(f"C1 period[{i}].type", typ, got["type"])
            eq(f"C1 period[{i}].fromDate", frm, got["fromDate"])
            eq(f"C1 period[{i}].dueDate", due, got["dueDate"])
            eq(f"C1 period[{i}].principal", prin, got["principal"])
            for name, exp_v in (("interest", inter), ("fee", fee), ("penalty", pen),
                                ("total", tot), ("balance", bal),
                                ("totalOutstandingBalance", tob)):
                if exp_v is not None:
                    eq(f"C1 period[{i}].{name}", exp_v, got[name])

    # ---- C2..C5 scalars -------------------------------------------------------------------
    for cid, exp in COMMITTED.items():
        obs = caps[cid]["observed"]
        for k, v in exp.items():
            eq(f"{cid}.{k}", v, str(obs[k]))

    # ---- C4 full period table -------------------------------------------------------------
    rows = [p for p in caps["T42-CTL-P0A"]["observed"]["periods"] if p["type"] == "REPAYMENT"]
    if len(rows) != len(P0A_ROWS):
        bad.append(f"C4: {len(rows)} repayment rows, expected {len(P0A_ROWS)}")
    else:
        for i, (exp, got) in enumerate(zip(P0A_ROWS, rows)):
            for name, v in zip(("fromDate", "dueDate", "principal", "interest", "fee", "penalty",
                                "balance", "total", "totalOutstandingBalance"), exp):
                eq(f"C4 T42-CTL-P0A period[{i + 1}].{name}", v, got[name])

    # ---- C5 full period table -------------------------------------------------------------
    rows = [p for p in caps["T42-CTL-MEB"]["observed"]["periods"] if p["type"] == "REPAYMENT"]
    if len(rows) != len(MEB_ROWS):
        bad.append(f"C5: {len(rows)} repayment rows, expected {len(MEB_ROWS)}")
    else:
        for i, (exp, got) in enumerate(zip(MEB_ROWS, rows)):
            for name, v in zip(("fromDate", "dueDate", "principal", "interest", "balance", "total"), exp):
                eq(f"C5 T42-CTL-MEB period[{i + 1}].{name}", v, got[name])

    print(f"T42 controls: {checked} cells compared against TRANSCRIBED literals "
          f"(shipped test + four committed captures taken by other harnesses).")
    if bad:
        print()
        for b in bad:
            print("  MISMATCH  " + b)
        print()
        print(f"FAIL -- {len(bad)} of {checked} cells do not reproduce.  This run is not comparable "
              f"to the committed corpus.")
        return 1
    print("PASS -- every control cell reproduces digit for digit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
