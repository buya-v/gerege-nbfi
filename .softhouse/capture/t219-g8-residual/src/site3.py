#!/usr/bin/env python3
"""
T229 — SITE 3's rescue condition, DERIVED FROM THE PINNED SOURCE, not fitted to any cell.

NO FLOATING POINT ANYWHERE (P-25). Every value on a decision path is `int` minor units,
`fractions.Fraction`, or `decimal.Decimal` under an explicit Context. There is no `float()` call
and no float literal on any decision path in this file.

The oracle is the Fineract reference implementation at pinned commit
426a23544e8426a38ae43ae404670a0a7e85b9eb. Oracle Database is a prohibited product in this program
and appears nowhere in this work.

=====================================================================================
THE DERIVATION — citations BOUND BY CONTENT (the quoted text is what was matched)
=====================================================================================

SCOPE. The G-8 shape only: MONTHS / repaymentEvery 1 / DECLINING_BALANCE / DAYS_30 / DAYS_360 /
single disbursement on the schedule start date / no down payment / no charges / both multiples-of
null / (19, HALF_UP) / minorUnitDigits = 2 / FRESH schedule, nothing paid, nothing re-aged,
nothing credited, no interest pause, no moratorium.

S3.0  Site 3 runs on FIRST schedule generation.
      ProgressiveEMICalculator.calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod
      bound by content:
        "final boolean onlyOnActualModelShouldApply = scheduleModel.isEmpty()"
        "calculateLastUnpaidRepaymentPeriodEMI(scheduleModel, calculateFromRepaymentPeriodDueDate);"
        "if (onlyOnActualModelShouldApply) {"
        "    checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods(scheduleModel, relatedRepaymentPeriods);"
      => on a fresh model the schedule is empty, so site 3 DOES run, and it runs AFTER
         calculateLastUnpaidRepaymentPeriodEMI.

S3.1  What the last period's EMI is when site 3 is entered.
      calculateLastUnpaidRepaymentPeriodEMI, bound by content:
        "Money diff = totalDisbursedAmount.plus(totalCapitalizedIncome, mc).plus(scheduleModel.getTotalCreditedPrincipal(), mc)
                 .plus(totalDueInterest, mc).minus(totalEMI, mc);"
        "Money adjustedEmi = repaymentPeriod.getEmi().add(diff, mc);"
      On the G-8 shape capitalizedIncome = creditedPrincipal = 0, so
        diff = B + SUM(dueInterest_k) - SUM(emi_k).

S3.2  dueInterest is CLAMPED TO THE INSTALMENT.  RepaymentPeriod.getDueInterest, bound by content:
        ": MathUtil.min(getCalculatedDueInterest(), getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest(), false),"
      and RepaymentPeriod.getDuePrincipal, bound by content:
        "return MathUtil.max(MathUtil
                .negativeToZero(getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().minus(getDueInterest(), getMc()), getMc()),
                getPaidPrincipal(), false);"
      => duePrincipal_k = max(0, EMI_k - I_k) where I_k = calculatedDueInterest_k, and
         dueInterest_k = min(I_k, EMI_k).

      THEREFORE, in the non-amortizing regime E <= I_1 (no principal ever leaves, so the balance
      never moves and I_k is the same every period before carry):
            SUM(dueInterest_k) = n*E   and   SUM(emi_k) = n*E
            ==>  diff = B  EXACTLY, for every n, however far E is below I_1.
      This is the single fact T223's site-3 note is missing. `diff` does NOT grow with the
      interest deficit, because the deficit is clamped out of `dueInterest` before it is summed.

S3.3  The quantization of I_k.  RepaymentPeriod.calculateCalculatedDueInterest, bound by content:
        "calculatedDueInterest = Money.of(getEmi().getCurrencyData(),
                getInterestPeriods().stream().map(InterestPeriod::getCalculatedDueInterest).reduce(BigDecimal.ZERO, BigDecimal::add),
                mc);"
      and Money's private constructor, bound by content:
        "this.amount = amountScaled.setScale(currency.getDecimalPlaces(), getMc().getRoundingMode());"
      => I_1 is B*r QUANTIZED to 2 places HALF_UP, NOT the exact product.
      (T223's predicate compares against the EXACT product. The code compares against the
       quantized one. On the cells to hand the two agree, but the code says quantized.)

S3.4  The deficit CARRIES.  RepaymentPeriod.calculateCalculatedDueInterest, bound by content:
        "if (getPrevious().isPresent()) {
            calculatedDueInterest = calculatedDueInterest.add(getPrevious().get().getUnrecognizedInterest(), getMc());"
      and RepaymentPeriod.getUnrecognizedInterest, bound by content:
        "return MathUtil.negativeToZero(getCalculatedDueInterest().minus(getDueInterest(), getMc()), getMc());"
      => with delta := I_1q - E >= 0 the unrecognized interest of period k is U_k = k*delta.

S3.5  What getEmiAdjustment hands to site 3.  ProgressiveEMICalculator.getEmiAdjustment,
      bound by content:
        "if (!lastPeriod.isFullyPaid() && !penultimatePeriod.isFullyPaid()) {
                Money emiDifference = lastPeriod.getEmi().minus(penultimatePeriod.getEmi());
                return new EmiAdjustment(penultimatePeriod.getEmi(), emiDifference, repaymentPeriods,
                        getUncountablePeriods(repaymentPeriods, penultimatePeriod.getEmi()));"
      Nothing is paid, so the first iteration (idx = n-1) returns immediately:
        originalEmi     = E
        emiDifference   = (E + diff) - E = diff = B          [by S3.1 + S3.2]
        related periods = all n
        uncountable     = 0, since getUncountablePeriods counts
                          "originalEmi.isLessThan(repaymentPeriod.getTotalPaidAmount())" and every
                          totalPaidAmount is zero.

S3.6  GUARD 1 — EmiAdjustment.shouldBeAdjusted, bound by content:
        "double lowerHalfOfRelatedPeriods = Math.floor(numberOfRelatedPeriods() / 2.0);
        return lowerHalfOfRelatedPeriods > 0.0 && !emiDifference.isZero() && emiDifference.abs()
                .multipliedBy(100)
                .isGreaterThan(originalEmi.copy(lowerHalfOfRelatedPeriods));"
      `multipliedBy(100)` binds the (long) overload -> exact, then re-quantized to 2 places;
      `copy(double)` -> "return copy(BigDecimal.valueOf(amount));" -> Money at 2 places.
      Both sides are MAJOR units, so in MINOR units the test is exactly
            |diff_minor| > floor(n/2).
      (|x|*100 major == x_minor; floor(n/2) major == floor(n/2)*100 minor; divide by 100.)

S3.7  GUARD 2 — the adjustment must be a non-zero number of minor units.
      EmiAdjustment.adjustment, bound by content:
        "return emiDifference.dividedBy(Math.max(1, numberOfRelatedPeriods() - uncountablePeriods));"
      -> Money.dividedBy(long) -> "Money.of(getCurrencyData(), newAmount, getMc())" -> 2 places
      HALF_UP.  So  a_minor = HALF_UP(diff_minor / n) = floor(diff_minor/n + 1/2) for diff > 0.
      Site 3 then does, bound by content:
        "if (adjustedEqualMonthlyInstallmentValue.isEqualTo(emiAdjustment.originalEmi())) {
                break;"
      => a_minor = 0 breaks out.  NOTE: for diff > 0, GUARD 1 (diff_minor > floor(n/2)) already
      implies a_minor >= 1.  **T223's second conjunct "2*B_minor >= n" is therefore REDUNDANT,
      not a second condition.**

S3.8  GUARD 3 — THE ONE T223 OMITS, AND THE ONE THAT DECIDES THE REGION.
      Site 3, bound by content:
        "calculateLastUnpaidRepaymentPeriodEMI(newScheduleModel, relatedPeriodsFirstDueDate);
            if (!getEmiAdjustment(newScheduleModel.repaymentPeriods()).hasLessEmiDifference(emiAdjustment)) {
                break;"
      with EmiAdjustment.hasLessEmiDifference, bound by content:
        "return emiDifference.abs().isLessThan(previousAdjustment.emiDifference.abs());"
      The raised instalment E' = E + a is applied to a COPY; the copy's own emiDifference must be
      STRICTLY SMALLER in absolute value, or the loop breaks and **the copy is discarded** — the
      write-back
        "relatedRepaymentPeriod.setEmi(newRepaymentPeriod.getEmi());"
      is below the break and never runs.

      If E' <= I_1q the copy is in the SAME non-amortizing regime, so by S3.2 its diff is B again:
      |diff'| = |diff| = B, NOT strictly less, so it BREAKS AND NOTHING CHANGES.
      Principal only flows, and diff only shrinks, when E' > I_1q, i.e. when a > delta.

=====================================================================================
THE LAW (registered before any probe)
=====================================================================================
In integer minor units, with  E = the instalment set on periods 1..n-1,
                              I1q = HALF_UP-quantize(B_minor * r) to whole minor units,
                              delta = I1q - E,
                              a = floor(B_minor/n + 1/2):

    SITE 3 RESCUES  <=>  B_minor > floor(n/2)  AND  a > delta
                    <=>  2*B_minor >= (2*delta + 1) * n          [for delta >= 1 the first
                                                                  conjunct is implied]

    T223's rule is EXACTLY this law with delta forced to 0 (2*B >= n). That is the whole error.

And the shape of an UNRESCUED cell follows from S3.1 + S3.4:
    last period EMI      = E + B
    last period interest = min(I1q + (n-1)*delta,  E + B)
    TOTAL PRINCIPAL REPAID = max(0, B_minor - n*delta)
      => FULL family B (principal column sums to 0.00)  <=>  delta >= 1 AND B_minor <= n*delta
      => PARTIAL family B                               <=>  delta >= 1 AND
                                                             n*delta < B_minor < (delta + 1/2)*n
                                                             and it repays exactly B_minor-n*delta
      => delta = 0                                      => the last row repays the WHOLE principal
    TOTAL INTEREST = n*E + B  for any unrescued cell.
"""

import datetime
import json
import sys
from decimal import Decimal, Context, ROUND_HALF_UP, ROUND_DOWN
from fractions import Fraction

sys.path.insert(0, __file__.rsplit('/', 1)[0])
import emi_mechanism_t223 as T223  # noqa: E402  (T223's committed digit-for-digit EMI emulator)

WIDE = Context(prec=400, rounding=ROUND_HALF_UP)


def half_up_div(num: int, den: int) -> int:
    """HALF_UP(num/den) on non-negative integers, exact integer arithmetic only."""
    assert den > 0
    neg = num < 0
    num = -num if neg else num
    q = (2 * num + den) // (2 * den)
    return -q if neg else q


def quantize_minor(exact: Fraction) -> int:
    """HALF_UP quantization of an exact minor-unit quantity to a whole minor unit."""
    return half_up_div(exact.numerator, exact.denominator) if exact >= 0 else -half_up_div(
        -exact.numerator, exact.denominator)


def predict(rate_str: str, n: int, b_minor: int, minor_digits: int = 2,
            start=datetime.date(2024, 1, 1)) -> dict:
    t = T223.predict(rate_str, n, b_minor, minor_digits, start)
    e = int(t["emiQuantizedMinor"])
    i1_exact = Fraction(int(t["i1ExactMinorNum"]), int(t["i1ExactMinorDen"]))
    i1q = quantize_minor(i1_exact)                       # S3.3
    delta = i1q - e
    a = half_up_div(b_minor, n)                          # S3.7, with diff = B (S3.2/S3.5)
    guard1 = (n >= 2) and (b_minor != 0) and (b_minor > n // 2)   # S3.6
    guard2 = a != 0                                              # S3.7
    guard3 = (delta >= 0) and (a > delta)                         # S3.8
    rescue = bool(guard1 and guard2 and guard3)
    if delta < 0:
        outcome, principal = "AMORTIZES_NORMALLY", b_minor
    elif rescue:
        outcome, principal = "RESCUED_BY_SITE3", None            # schedule re-derived; not modelled
    elif delta == 0:
        outcome, principal = "LAST_ROW_CARRIES_ALL_PRINCIPAL", b_minor
    else:
        principal = max(0, b_minor - n * delta)
        outcome = "FAMILY_B_FULL" if principal == 0 else "FAMILY_B_PARTIAL"
    return {
        "id": None, "rate": rate_str, "n": n, "bMinor": b_minor,
        "emiMinorPredicted": e, "i1ExactMinor": str(i1_exact), "i1QuantizedMinor": i1q,
        "deltaMinor": delta, "aMinor": a,
        "guard1_shouldBeAdjusted": guard1, "guard2_nonZeroAdjustment": guard2,
        "guard3_hasLessEmiDifference": guard3,
        "site3Rescues": rescue,
        "predictedOutcome": outcome,
        "predictedTotalPrincipalMinor": principal,
        "predictedTotalInterestMinor": (None if outcome == "RESCUED_BY_SITE3"
                                        else n * e + b_minor),
        "predictedLastRowTotalMinor": (None if outcome == "RESCUED_BY_SITE3" else e + b_minor),
        "t223Rule_rescues": bool(b_minor > n // 2 and 2 * b_minor >= n),
    }


if __name__ == "__main__":
    cells = json.load(open(sys.argv[1]))
    out = []
    for c in cells:
        p = predict(c["rate"], c["n"], c["bMinor"])
        p["id"] = c["id"]
        out.append(p)
    json.dump(out, sys.stdout, indent=1)
    print()
