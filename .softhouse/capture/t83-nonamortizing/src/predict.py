#!/usr/bin/env python3
"""T83 — PREDICTION GENERATOR. Run BEFORE any probe; its output is committed as
part of PREDICTION.md and predicted-boundary.json.

WHAT THIS IS. A closed-form guess at where the non-amortizing region ends, from
the mechanism T74/T75 named in source, so that the sweep can be judged against a
number registered in advance. It is NOT a capture and NOTHING it prints may ever
be transcribed into a vector.

THE MECHANISM, as T75 reported it (RepaymentPeriod.java:371-372, :389-402;
ProgressiveEMICalculator.java:1160,:1178-1181,:1210):

  every repayment period's EMI quantizes to 0.00
    -> isFullyPaid() is vacuously true on all of them (0 == 0)
    -> findLastUnpaidRepaymentPeriod is empty
    -> calculateLastUnpaidRepaymentPeriodEMI takes its fallback branch, whose
       filter populates the last period's outstanding-balance memo while
       duePrincipal is still 0, then raises that period's EMI through a plain
       setter that does not invalidate the memo
    -> the emitted balance column is stale and never reaches zero.

So the predicted trigger is exactly "the level EMI quantizes to zero", i.e.

    B_minor * a(r, n) < 0.5          with HALF_UP at scale 2

where a(r, n) = r / (1 - (1+r)^-n) is the ordinary annuity factor and
r = annual / 100 / 12 (the DAYS_30/DAYS_360 monthly rate).

Largest predicted failing principal  = ceil(0.5 / a) - 1  minor units.
Smallest predicted clean principal   = that + 1.

This is a HYPOTHESIS. The measured boundary is whatever the oracle emits.
"""
from decimal import Decimal, getcontext
import json
import math

getcontext().prec = 60

RATES = ["21.6", "7.0", "16.8", "36.0"]
TERMS = [2, 3, 4, 6, 12, 24, 36, 56]


def annuity_factor(rate: str, n: int) -> Decimal:
    r = Decimal(rate) / Decimal(100) / Decimal(12)
    return r / (1 - (1 + r) ** Decimal(-n))


def rows():
    out = []
    for rate in RATES:
        for n in TERMS:
            a = annuity_factor(rate, n)
            thr = Decimal("0.5") / a
            largest_fail = math.ceil(thr) - 1
            sweep_hi = max(largest_fail + 4, 5)
            out.append({
                "annualRatePct": rate,
                "numberOfRepayments": n,
                "annuityFactor": f"{a:.10f}",
                "halfOverFactor": f"{thr:.6f}",
                "predictedLargestFailingMinor": largest_fail,
                "predictedSmallestCleanMinor": largest_fail + 1,
                "sweepFromMinor": 1,
                "sweepToMinor": sweep_hi,
            })
    return out


if __name__ == "__main__":
    r = rows()
    print(json.dumps({
        "note": "PREDICTION ONLY. Not an observation. Never promotable.",
        "mechanism": "level EMI quantizes to 0.00 at scale 2 under HALF_UP",
        "rule": "fails iff B_minor * a(r,n) < 0.5",
        "rows": r,
        "totalSweepCases": sum(x["sweepToMinor"] for x in r),
    }, indent=1))
