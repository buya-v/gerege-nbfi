#!/usr/bin/env python3
"""T44 AUDIT -- independent re-transcription of two of T42's five controls.

Literals re-read by the auditor from the primary sources, NOT copied from
.softhouse/capture/mathcontext/analysis/controls.py:

  A1  T42-CAL     shipped test EmbeddableProgressiveLoanScheduleGeneratorTest.java
                  (MathContext(12, HALF_UP); 182 / 100.00 / 2.05 / 102.05; 7 periods)
  A2  T42-CTL-P0A committed capture T39-P0-A, .softhouse/handoff/T39-periodratio-observation.md
                  section 2 worked example (full 6-row table + 4 plan scalars)

Exact string comparison.  No float anywhere.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(os.path.join(HERE, "..", "..", "..", "mathcontext", "out", "t42-mathcontext.json"))
by = {c["id"]: c for c in json.load(open(P))["captures"]}

fails = []
lines = []


def eq(tag, got, want):
    if str(got) != str(want):
        fails.append("%s: observed %r != transcribed %r" % (tag, str(got), str(want)))


# ---- A1 : shipped test literal (re-read by the auditor from the pinned checkout) ----------
cal = by["T42-CAL"]["observed"]
eq("CAL.loanTermInDays", cal["loanTermInDays"], "182")
eq("CAL.totalDisbursedAmount", cal["totalDisbursedAmount"], "100.00")
eq("CAL.totalInterestAmount", cal["totalInterestAmount"], "2.05")
eq("CAL.totalRepaymentAmount", cal["totalRepaymentAmount"], "102.05")
CAL_ROWS = [
    # principal, interest, fee, penalty, total, balance, totalOutstandingBalance
    ("16.43", "0.58", "0.00", "0.00", "17.01", "83.57", "85.04"),
    ("16.52", "0.49", "0.00", "0.00", "17.01", "67.05", "68.03"),
    ("16.62", "0.39", "0.00", "0.00", "17.01", "50.43", "51.02"),
    ("16.72", "0.29", "0.00", "0.00", "17.01", "33.71", "34.01"),
    ("16.81", "0.20", "0.00", "0.00", "17.01", "16.90", "17.00"),
    ("16.90", "0.10", "0.00", "0.00", "17.00", "0.00", "0.00"),
]
eq("CAL.periods", len(cal["periods"]), 7)
eq("CAL.disbursement.principal", cal["periods"][0]["principal"], "100.00")
for i, row in enumerate(CAL_ROWS, start=1):
    p = cal["periods"][i]
    for k, want in zip(("principal", "interest", "fee", "penalty", "total", "balance",
                        "totalOutstandingBalance"), row):
        eq("CAL.p%d.%s" % (i, k), p[k], want)

# ---- A2 : T39-P0-A, re-read by the auditor from the T39 handoff ---------------------------
p0a = by["T42-CTL-P0A"]["observed"]
eq("P0A.loanTermInDays", p0a["loanTermInDays"], "185")
eq("P0A.totalDisbursedAmount", p0a["totalDisbursedAmount"], "1200000.00")
eq("P0A.totalInterestAmount", p0a["totalInterestAmount"], "76984.00")
eq("P0A.totalRepaymentAmount", p0a["totalRepaymentAmount"], "1276984.00")
P0A_ROWS = [
    # from, due, principal, interest, fee, penalty, balance, total, totalOutstandingBalance
    ("2024-01-28", "2024-02-29", "192580.67", "20250.00", "0.00", "0.00", "1007419.33", "212830.67", "1064153.33"),
    ("2024-02-29", "2024-03-31", "193527.22", "19303.45", "0.00", "0.00", "813892.11", "212830.67", "851322.66"),
    ("2024-03-31", "2024-04-30", "198180.61", "14650.06", "0.00", "0.00", "615711.50", "212830.67", "638491.99"),
    ("2024-04-30", "2024-05-31", "201390.35", "11440.32", "0.00", "0.00", "414321.15", "212830.67", "425661.32"),
    ("2024-05-31", "2024-06-30", "205372.89", "7457.78", "0.00", "0.00", "208948.26", "212830.67", "212830.65"),
    ("2024-06-30", "2024-07-31", "208948.26", "3882.39", "0.00", "0.00", "0.00", "212830.65", "0.00"),
]
for i, row in enumerate(P0A_ROWS, start=1):
    p = p0a["periods"][i]
    for k, want in zip(("fromDate", "dueDate", "principal", "interest", "fee", "penalty",
                        "balance", "total", "totalOutstandingBalance"), row):
        eq("P0A.p%d.%s" % (i, k), p[k], want)

n = 4 + 1 + 6 * 7 + 4 + 6 * 9
print("T44 audit controls: %d cells re-transcribed by the auditor and compared exact-string." % n)
if fails:
    for f in fails:
        print("  MISMATCH " + f)
    print("FAIL")
    sys.exit(1)
print("PASS -- both re-transcribed controls reproduce digit for digit.")

# ---- failability of THIS script ----------------------------------------------------------
if os.environ.get("AUDIT_SELFTEST") == "1":
    fails2 = []
    if str(cal["totalInterestAmount"]) != "2.06":
        fails2.append("selftest: deliberately wrong expectation 2.06 correctly rejected")
    print("SELFTEST:", fails2[0] if fails2 else "SELFTEST DID NOT FIRE -- bad")
    sys.exit(1 if fails2 else 2)
