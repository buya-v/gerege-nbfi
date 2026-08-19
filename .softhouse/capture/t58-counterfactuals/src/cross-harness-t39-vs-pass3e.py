#!/usr/bin/env python3
"""T58 — cross-harness reproduction check: pass 3e against task T39's capture.

Pass 3e asks the pinned reference oracle the SAME FOURTEEN REQUESTS task T39 asked
two fires ago, through a DIFFERENT Path A harness (Capture3e.java, descended from
pass 3b, against T39's CapturePeriodRatio.java). This script compares the two
observations cell for cell.

It is not a calibration in the runner's sense -- the runner already enforces three
of those against committed artefacts and refuses the run on drift. It is an
independent corroboration, reported rather than enforced, and its result is
recorded in the handoff whichever way it comes out.

Column names differ between the two harnesses (T39: fromDate/fee/penalty; pass 3e:
periodFromDate/feeAmount/penaltyAmount), so the comparison is by MEANING, and the
mapping is written out below rather than inferred. Money is compared as the
oracle's own emitted CHARACTERS -- no parsing, no float, no normalisation -- so a
scale difference would be reported as a difference rather than smoothed away.

Run from the repository root:

    python3 .softhouse/capture/t58-counterfactuals/src/cross-harness-t39-vs-pass3e.py
"""

import json
import sys

T39 = ".softhouse/capture/periodratio/out/t39-periodratio.json"
P3E = ".softhouse/capture/out/capture-prod3e-raw.json"

# pass-3e case id -> T39 case id. Written out, never inferred from the purpose text.
PAIRS = {
    "P-DRIFT-A": "T39-P0-A", "P-DRIFT-B": "T39-P0-B", "P-DRIFT-C": "T39-P0-C",
    "P-DRIFT-D": "T39-P0-D", "P-DRIFT-E": "T39-P0-E", "P-DRIFT-F": "T39-P0-F",
    "P-DRIFT-G": "T39-P0-G", "P-DRIFT-H": "T39-P0-H",
    "P-ME-A": "T39-ME-A", "P-ME-B": "T39-ME-B", "P-ME-C": "T39-ME-C", "P-ME-D": "T39-ME-D",
    "P-LAT-Q0a": "T39-CTL-Q0a", "P-LAT-MID": "T39-CTL-2",
}

# the inputs both harnesses record under the same key and that define the request
INPUT_KEYS = [
    "scheduleGenerationStartDate", "disbursementDate", "disbursementAmount",
    "numberOfRepayments", "repaymentFrequencyType", "annualNominalInterestRate",
    "mathContextPrecision", "mathContextRoundingMode", "currencyCode",
    "currencyDecimalPlaces", "daysInMonth", "daysInYear", "interestMethod",
    "allowPartialPeriodInterestCalculation", "allowFullTermForTranche",
    "downPaymentEnabled", "fixedLength", "installmentAmountInMultiplesOf",
]

# plan-level columns both harnesses emit
PLAN_KEYS = ["loanTermInDays", "totalDisbursedAmount", "totalInterestAmount",
             "totalRepaymentAmount"]

# per-row columns, as (T39 key, pass-3e key)
ROW_KEYS = [
    ("type", "type"), ("periodNumber", "periodNumber"),
    ("fromDate", "periodFromDate"), ("dueDate", "dueDate"),
    ("principal", "principal"), ("interest", "interest"), ("balance", "balance"),
    ("fee", "feeAmount"), ("penalty", "penaltyAmount"),
    ("total", "total"), ("totalOutstandingBalance", "totalOutstandingBalance"),
]


def main():
    t39 = {c["id"]: c for c in json.load(open(T39))["captures"]}
    p3e = {c["id"]: c for c in json.load(open(P3E))["captures"]}

    cells = rows = diffs = 0
    problems = []
    for mine, theirs in sorted(PAIRS.items()):
        a, b = p3e[mine], t39[theirs]

        for k in INPUT_KEYS:
            av, bv = a["inputs"].get(k), b["inputs"].get(k)
            cells += 1
            if av != bv:
                diffs += 1
                problems.append("%s vs %s: INPUT %s  pass3e=%r  T39=%r" % (mine, theirs, k, av, bv))
        # T39 spells it repaymentEvery, pass 3e repaymentFrequency; same quantity.
        cells += 1
        if a["inputs"].get("repaymentFrequency") != b["inputs"].get("repaymentEvery"):
            diffs += 1
            problems.append("%s vs %s: INPUT repaymentEvery pass3e=%r T39=%r"
                            % (mine, theirs, a["inputs"].get("repaymentFrequency"),
                               b["inputs"].get("repaymentEvery")))

        for k in PLAN_KEYS:
            av, bv = a["observed"].get(k), b["observed"].get(k)
            cells += 1
            if av != bv:
                diffs += 1
                problems.append("%s vs %s: PLAN %s  pass3e=%r  T39=%r" % (mine, theirs, k, av, bv))

        pa, pb = a["observed"]["periods"], b["observed"]["periods"]
        if len(pa) != len(pb):
            diffs += 1
            problems.append("%s vs %s: ROW COUNT pass3e=%d T39=%d" % (mine, theirs, len(pa), len(pb)))
            continue
        for i, (ra, rb) in enumerate(zip(pa, pb)):
            rows += 1
            for kb, ka in ROW_KEYS:
                av, bv = ra.get(ka), rb.get(kb)
                if av is None and bv is None:
                    continue          # neither harness recorded it -- nothing to compare
                if bv is None:
                    continue          # T39 did not record it; pass 3e recording MORE is the point
                cells += 1
                if av != bv:
                    diffs += 1
                    problems.append("%s vs %s: row %d %s  pass3e=%r  T39=%r"
                                    % (mine, theirs, i, kb, av, bv))

    print("CROSS-HARNESS REPRODUCTION -- pass 3e (Capture3e.java) against T39 (CapturePeriodRatio.java)")
    print("  case pairs compared      %d" % len(PAIRS))
    print("  schedule rows compared   %d" % rows)
    print("  cells compared           %d" % cells)
    print("  DIFFERENCES              %d" % diffs)
    for p in problems:
        print("    " + p)
    print()
    print("NOTE: pass 3e records outstandingLoanBalance on the DISBURSEMENT row and T39 does not.")
    print("      A column T39 never recorded is skipped rather than compared against nothing --")
    print("      pass 3e recording MORE than T39 is the whole reason this pass exists.")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
