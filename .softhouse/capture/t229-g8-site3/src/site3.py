#!/usr/bin/env python3
"""
T229 — SITE 3's rescue condition, DERIVED FROM THE PINNED SOURCE, not fitted to any cell.

*********************************************************************************************
*** T241 CORRECTION, added at a LATER commit than the rest of this file. READ THIS FIRST. ***
*********************************************************************************************

ONE SENTENCE OF THIS FILE IS FALSE, AND ITS OUTPUT FIELD `predictedTotalInterestMinor` IS WRONG
ON EVERY CELL THAT REPAYS ANY PRINCIPAL AT ALL.

    THE FALSE CLAIM (docstring, THE LAW, last line; and the value of
    `predictedTotalInterestMinor`):        TOTAL INTEREST = n*E + B  for any unrescued cell
    THE CORRECT FORM:                      TOTAL INTEREST = n*E + B - (principal repaid)

`n*E + B` IS NOT THE TOTAL INTEREST. IT IS THE TOTAL REPAYMENT. Only the LABEL is wrong; the
quantity is right and this file's derivation of it is right. On the G-8 shape there are no fees
and no penalties, so each row's `total` is `interest + principal`, and by this file's OWN S3.1 and
S3.5 the total column is `(n-1)*E + (E + B) = n*E + B`. Subtracting the principal column gives the
interest column. **The corrected form is a consequence of steps this file already derived**, not a
new mechanism, and it needed no new measurement.

WHY THE ERROR SURVIVED THE PROBE THAT WAS DESIGNED TO CATCH IT: on a FULL family-B cell the
principal repaid is 0, so the two formulas COINCIDE. The error is invisible on exactly the shape
T229 was hunting.

NOTHING IS EDITED BELOW — no line of T229's text is removed or reworded, no value this file
computes is changed, and no output key is added or renamed, so `python3 src/site3.py
src/cells-t229.json` still reproduces the committed `../prediction.json` BYTE FOR BYTE (T241
verified this before and after adding these comments). That is deliberate: `prediction.json` is
the REGISTERED prediction whose strict-ancestor commit is the falsifiability guarantee
(`29ed78c` prediction  ->  `bb35cc8` capture), and silently improving the instrument would destroy
the thing this directory exists to preserve (T114's ruling, T176's prohibition). The correction is
therefore a LABELLED annotation, and the field below still emits the WRONG number by design.
**A reader must apply the correction; the file will not apply it for them.**

WHICH MEASUREMENT ESTABLISHES IT, AND AT WHICH COMMIT:

  * T219's live oracle capture, committed at `6eacc06` in
    `.softhouse/capture/t219-g8-residual/out/capture-t219-raw.json.gz`:
        T219-R600p0-N3000-B3001 : n=3000, E=1500, B=3001, principal repaid = 1
                                  n*E + B = 4503001   OBSERVED total interest = 4503000
        T219-R600p0-N3000-B4499 : n=3000, E=2249, B=4499, principal repaid = 1499
                                  n*E + B = 6751499   OBSERVED total interest = 6750000
    In both cases `n*E + B` equals the OBSERVED TOTAL REPAYMENT exactly (4503001 and 6751499), and
    the overstatement of interest equals the principal repaid exactly.

  * **AND T229's OWN CAPTURE ALREADY CONTAINED THREE COUNTEREXAMPLES**, committed at `bb35cc8` in
    `../out/capture-t229-raw.json.gz` — B201 (overstates by 1), B251 (by 51), B299 (by 99).
    T229's own `classify_t229.py` COMPUTED the check and wrote
    `"P2_totalInterestEqualsNEplusB": false` for all three into `../out/classify-t229.json`. It was
    not read, because the `verdict` field in `classify_t229.py` is a function of the observed
    OUTCOME and the observed PRINCIPAL only and never consults P2 — so all three were reported
    "AS PREDICTED". The refutation was measured, printed and committed on the same day as the
    claim. **This is a P-69 instance in its purest form: the evidence was not missing, it was
    unread.**

RE-DERIVED INDEPENDENTLY BY T241 from the raw captured rows (not transcribed from T219, whose
handoff warns that transcription is how this section acquires its defects). The re-derivation is
committed beside this file as `rederive_total_interest_t241.py`; it re-reads the `.gz` captures,
sums the interest and principal COLUMNS, cross-checks them against the reported totals, asserts the
per-row `total == interest + principal` identity, and exits non-zero if any leg fails. T241's
figures AGREE with T219's on both named cells.

MATERIALITY: **LOW, and it must not be inflated.** This field affects NO verdict anywhere.
`classify_t229.py` grades on outcome and principal; no gate conclusion, no vector, no promoted
figure and no region boundary is computed from `predictedTotalInterestMinor`. `.softhouse/gates.md`
already carries the CORRECT form under *THE LAW*, so the LIVE text was right and only this
committed instrument was wrong — the reverse of the usual direction, which is why it was easy to
miss. Nothing about G-8's region, its conservative superset `B_minor < 1.5*n`, or the standing
prohibition on putting options (b)/(c) to Buyan is touched by this correction.

*********************************** END T241 CORRECTION *************************************

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
    *** T241 CORRECTION — THE LINE DIRECTLY ABOVE IS FALSE AND IS KEPT VERBATIM AS THE RECORD.
        n*E + B is the TOTAL REPAYMENT.  TOTAL INTEREST = n*E + B - (principal repaid), i.e.
        n*E + B - max(0, B_minor - n*delta) on an unrescued cell, which is n*E + B only when the
        principal repaid is 0 (FULL family B).  Established by T219's capture at 6eacc06 (B3001,
        B4499) and by THIS DIRECTORY'S OWN capture at bb35cc8 (B201, B251, B299); re-derived
        independently in rederive_total_interest_t241.py.  See the T241 CORRECTION banner at the
        top of this docstring.  Affects no verdict. ***
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
        # *** T241 CORRECTION — THIS FIELD IS WRONG AND IS DELIBERATELY LEFT WRONG. ***
        # `n * e + b_minor` is the TOTAL REPAYMENT, not the total interest. The correct value is
        # `n * e + b_minor - principal`, and the two coincide only when `principal == 0`
        # (FULL family B). It is NOT fixed here because this file must keep reproducing the
        # registered `../prediction.json` byte for byte; fixing it would silently rewrite a
        # committed prediction (T114/T176). Do not read this field. Affects no verdict — nothing
        # in classify_t229.py's `verdict` consults it. See the banner at the top of this file.
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
