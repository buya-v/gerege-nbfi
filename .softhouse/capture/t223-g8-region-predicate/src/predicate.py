#!/usr/bin/env python3
"""
T223 — THE PREDICATE for gate G-8's region, derived from the mechanism.

Registered in ../PREDICTION.md, in a commit that is a STRICT ANCESTOR of the commit carrying any
probe output (P-9). Nothing here is fitted: every constant in it is read off a source site.

Exact arithmetic only (P-25): int minor units, Fraction, Decimal. No float on any path.

------------------------------------------------------------------------------------------------
THE THREE SITES, re-verified BY CONTENT at pinned `426a23544e8426a38ae43ae404670a0a7e85b9eb`
------------------------------------------------------------------------------------------------
S1  ProgressiveEMICalculator.java:1962  `.divide(calculatedDaysInPeriod, mc)
                                          .setScale(mc.getPrecision(), mc.getRoundingMode())`
    -- precision 19 consumed as DECIMAL PLACES. [VERIFIED, quoted text present at that line]
S2  RepaymentPeriod.java:217            `interestPeriods.stream().map(InterestPeriod::getRateFactor)
                                          .reduce(BigDecimal.ONE, BigDecimal::add)`
    -- the two-argument add, NO MathContext. [VERIFIED, quoted text present at that line]
S3  ProgressiveEMICalculator.java:1258-1308  checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods,
    with EmiAdjustment.shouldBeAdjusted() / adjustment() in
    fineract-progressive-loan/.../calc/data/EmiAdjustment.java.
    **S3 IS NOT IN T220's MECHANISM NOTE AND IT IS LOAD-BEARING**: it is the only reason a cell with
    an instalment at or below the first period's interest can still amortize.

------------------------------------------------------------------------------------------------
THE PREDICATE
------------------------------------------------------------------------------------------------
Let, in integer minor units,
    E_q  = the oracle's instalment, emulated digit-for-digit through S1+S2 and quantized by
           Money(..) (Money.java:40-53) to `d` places, HALF_UP;
    I_1  = B_minor * rateFactor_1, EXACTLY (a Fraction; rateFactor_1 comes out of S1).

    (1)  E_q  >  I_1   ->  NOT family B. Every period leaves E_q - I_1 > 0 for principal, so the
                           loan amortizes -- however slowly.
    (2)  E_q  == I_1   ->  NOT family B. No interest deficit accrues, so the last-period fallback's
                           residual is applied as PRINCIPAL and the principal column sums.
    (3)  E_q  <  I_1   ->  the instalment does not even cover the period's interest; the deficit
                           accrues as deferred interest and the last-period fallback's residual is
                           applied INTEREST-FIRST. Family B UNLESS S3 rescues it, which needs BOTH
                             (3a) shouldBeAdjusted():  B_minor * 100  >  E_q * floor(n/2)
                                  (the shortfall carried to the final row is exactly D = B_minor
                                   whenever nothing amortizes: total due interest == total EMI, so
                                   D = disbursed + totalDueInterest - totalEMI = B_minor)
                             (3b) adjustment() >= 1 minor unit:  round_HALF_UP(B_minor / n) >= 1,
                                  i.e.  2 * B_minor >= n
                           -> if (3a) and (3b): NOT family B. Otherwise: **FAMILY B**.

SCOPE, stated up front so it cannot silently widen:
  * FULL shape only. It makes NO claim about the PARTIAL family-B shape (7 measurements over 4
    shapes in the committed corpus), and it is not evidence about it either way.
  * The one graded shape: MONTHS / repaymentEvery 1 / DECLINING_BALANCE / DAYS_30 / DAYS_360 /
    single disbursement on the schedule start date 2024-01-01 / no down payment / no charges /
    both multiples-of null / (19, HALF_UP) / minorUnitDigits 2.
  * It says nothing about the THIRD OUTCOME (the oracle throwing instead of answering).
"""

import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emi_mechanism import predict as emi_predict  # noqa: E402


def classify(annual_pct_str, n, b_minor, minor_digits=2):
    p = emi_predict(annual_pct_str, n, b_minor, minor_digits)
    e_q = p["emiQuantizedMinor"]
    i1 = Fraction(p["i1ExactMinorNum"], p["i1ExactMinorDen"])
    if e_q > i1:
        verdict, branch = False, "(1) E_q > I_1 -- amortizes"
    elif e_q == i1:
        verdict, branch = False, "(2) E_q == I_1 -- residual lands as principal"
    else:
        should = b_minor * 100 > e_q * (n // 2)
        effective = 2 * b_minor >= n
        if should and effective:
            verdict, branch = False, "(3) rescued by the S3 EMI-adjustment loop"
        else:
            verdict = True
            branch = "(3) FAMILY B -- shouldBeAdjusted=%s adjustmentEffective=%s" % (should, effective)
    out = dict(p)
    out["familyB"] = verdict
    out["branch"] = branch
    return out
