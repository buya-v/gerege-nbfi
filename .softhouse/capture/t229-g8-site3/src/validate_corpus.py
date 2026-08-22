#!/usr/bin/env python3
"""T229 — test FACT A and the unrescued-shape law against EVERY committed raw capture.

FACT A            : on a cell whose principal column is stuck (row 1 principal == 0),
                    last-row total  -  row-1 total  ==  B, EXACTLY.
SHAPE LAW         : totalPrincipal == max(0, B - n*delta) with delta = row-1 interest - row-1 total
                    ... no: delta = I1q - E, and on a stuck cell row-1 interest == min(I1q, E) == E,
                    so delta is NOT observable from row 1. It IS observable as
                        delta = (I1q - E) where I1q = HALF_UP(B * r) and E = row-1 total.
                    r is taken from the cell's own annual rate (DAYS_30/DAYS_360, monthly).
TOTAL INTEREST    : n*E + B on every stuck cell.

INTEGER MINOR UNITS ONLY. No float anywhere. `.gz` raw captures only (STANDING RULE 5).
"""
import glob
import gzip
import json
import os
import sys
from decimal import Decimal
from fractions import Fraction


def minor(s):
    d = Decimal(str(s)) * 100
    assert d == d.to_integral_value(), s
    return int(d)


def half_up(num: Fraction) -> int:
    n, d = num.numerator, num.denominator
    return (2 * n + d) // (2 * d)


def rate_factor_minor(annual_pct: str) -> Fraction:
    """rateFactorByRepaymentEveryMonth with DAYS_30/DAYS_360, repaymentEvery 1, actual==calculated.
    Computed EXACTLY here as a Fraction. The oracle computes it at (19, HALF_UP) then setScale(19);
    where that differs from the exact value the cell is reported as RATE_FACTOR_INEXACT and skipped."""
    return Fraction(Decimal(annual_pct)) / 100 * Fraction(30, 360)


rows = []
for path in sorted(glob.glob(os.path.join(sys.argv[1], "**", "*.json.gz"), recursive=True)):
    raw = json.load(gzip.open(path))
    for c in raw.get("captures", []):
        inp = c.get("inputs") or {}
        if c.get("threw") or not c.get("observed"):
            continue
        if inp.get("repaymentFrequencyType") != "MONTHS" or inp.get("repaymentFrequency") != 1:
            continue
        if inp.get("daysInMonthType") not in (None, "DAYS_30") or \
           inp.get("daysInYearType") not in (None, "DAYS_360"):
            continue
        if str(inp.get("mathContextPrecision")) != "19":
            continue
        o = c["observed"]
        reps = [r for r in o["periods"] if r["type"] == "REPAYMENT"]
        if len(reps) < 2:
            continue
        b = minor(o["totalDisbursedAmount"])
        n = int(inp["numberOfRepayments"])
        if minor(reps[0]["principal"]) != 0:
            continue                      # not a stuck cell; nothing claimed
        e = minor(reps[0]["total"])
        rf = rate_factor_minor(str(inp["annualNominalInterestRate"]))
        i1q = half_up(Fraction(b) * rf)
        delta = i1q - e
        rows.append({
            "file": os.path.basename(path), "id": c["id"], "n": n, "bMinor": b, "eMinor": e,
            "i1q": i1q, "delta": delta,
            "factA_emiDiffEqualsB": (minor(reps[-1]["total"]) - e) == b,
            "emiDiffObserved": minor(reps[-1]["total"]) - e,
            "principalObserved": minor(o["totalPrincipalAmount"]),
            "principalPredicted": max(0, b - n * delta),
            "interestObserved": minor(o["totalInterestAmount"]),
            "interestPredicted": n * e + b,
        })

for r in rows:
    r["shapeLawHolds"] = r["principalObserved"] == r["principalPredicted"]
    r["interestLawHolds"] = r["interestObserved"] == r["interestPredicted"]

summary = {
    "stuckCellsExamined": len(rows),
    "factA_holds": sum(1 for r in rows if r["factA_emiDiffEqualsB"]),
    "shapeLaw_holds": sum(1 for r in rows if r["shapeLawHolds"]),
    "interestLaw_holds": sum(1 for r in rows if r["interestLawHolds"]),
    "deltaHistogram": {},
}
for r in rows:
    k = str(r["delta"])
    summary["deltaHistogram"][k] = summary["deltaHistogram"].get(k, 0) + 1
summary["failures"] = [r for r in rows if not (r["factA_emiDiffEqualsB"] and r["shapeLawHolds"]
                                               and r["interestLawHolds"])]
json.dump({"summary": summary, "rows": rows}, sys.stdout, indent=1)
print()
