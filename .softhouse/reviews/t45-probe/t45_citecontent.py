#!/usr/bin/env python3
"""T45 - CONTENT check on the load-bearing citations of DEC-1 revision 9.

The range check (t45_citecheck.py) proves a cited line EXISTS. It does not prove the line
says what the sentence above it claims -- and P1-T43-1 was a citation that existed, was
correctly formatted, and said the opposite of what it was cited for. So this probe asserts,
for every citation revision 9 touches plus the highest-value ones it inherits, that the
cited line or range CONTAINS an expected token.

Every assertion below was written by reading the pinned source, not by copying the document.
"""
import os
import subprocess
import sys

FIN = os.environ.get("FIN", "/Users/buv/fineract")

F = {
    "PLSG": "fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/ProgressiveLoanScheduleGenerator.java",
    "ACLSG": "fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/AbstractCumulativeLoanScheduleGenerator.java",
    "SCPP": "fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/ScheduleCurrentPeriodParams.java",
    "MONEY": "fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/Money.java",
    "MH": "fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/MoneyHelper.java",
    "EMI": "fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculator.java",
    "LSP": "fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/data/LoanScheduleParams.java",
    "LC": "fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/domain/LoanCharge.java",
    "LRSPW": "fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/domain/LoanRepaymentScheduleProcessingWrapper.java",
}

# (key, lo, hi, must-contain, what the document claims it is)
ASSERTIONS = [
    # ---- P1-T43-1 : the cumulative / progressive contrast
    ("ACLSG", 504, 504, "addTotalRepaymentExpected(feeChargesForInstallment.plus(penaltyChargesForInstallment))",
     "rev 8 cited this as the cumulative DIFFERENCE; rev 9 says it is the SHARED separated-path line"),
    ("PLSG", 486, 486, "addTotalRepaymentExpected(feeChargesForInstallment.plus(penaltyChargesForInstallment))",
     "the progressive twin of ACLSG:504"),
    ("ACLSG", 488, 508, "private void updatePeriodsWithCharges",
     "the cumulative generator's own updatePeriodsWithCharges"),
    ("PLSG", 470, 490, "private void updatePeriodsWithCharges",
     "the progressive generator's updatePeriodsWithCharges"),
    ("ACLSG", 349, 349, "applyChargesForCurrentPeriod(loanCharges",
     "cumulative: charges land on currentPeriodParams BEFORE the period total is taken"),
    ("ACLSG", 352, 352, "currentPeriodParams.fetchTotalAmountForPeriod()",
     "cumulative: the period total that carries the charges"),
    ("ACLSG", 392, 392, "addTotalRepaymentExpected(totalInstallmentDue)",
     "cumulative: THE real difference from the progressive generator"),
    ("SCPP", 144, 146, "feeChargesForInstallment",
     "fetchTotalAmountForPeriod = principal + interest + fee + penalty"),
    ("SCPP", 144, 146, "penaltyChargesForInstallment", "same"),
    ("PLSG", 137, 137, "addTotalRepaymentExpected(principalDue.plus(interestDue, mc))",
     "progressive: principal + interest, NO charge term"),
    ("PLSG", 367, 382, "addTotalFeeChargesCharged",
     "applyChargesForCurrentPeriod's whole body"),
    ("PLSG", 492, 504, "separateTotalCompoundingPercentageCharges",
     "the separated set :486 serves"),
    ("LSP", 211, 211, "chargesDueAtTimeOfDisbursement",
     "totalRepaymentExpected's seed"),
    ("LSP", 246, 246, "chargesDueAtTimeOfDisbursement", "the identical seed"),
    # ---- P2-T43-1 : the down-payment term
    ("PLSG", 345, 345, "addTotalRepaymentExpected(downPaymentAmount)",
     "the fourth contributor rev 8's C-1 omitted"),
    ("PLSG", 332, 332, "isDownPaymentEnabled()", "the branch that gates :345"),
    # ---- P1-T43-3 : M4 / M5
    ("PLSG", 400, 415, "getCumulativeAmountOfCharge",
     "the one routine all charge attribution funnels through"),
    ("PLSG", 403, 403, "isDueInPeriod(periodStart, periodEnd, isFirstPeriod)", "M4 itself"),
    ("PLSG", 404, 404, "isInstalmentFee() && isInstallmentChargeApplicable",
     "M5: the arm that does NOT read isDue"),
    ("PLSG", 405, 405, "calculateInstallmentCharge", "M5's effect"),
    ("PLSG", 406, 406, "isOverdueInstallmentCharge() && isDue", "an isDue arm -> M4"),
    ("PLSG", 408, 408, "isDue && loanCharge.getChargeCalculation().isPercentageBased()",
     "an isDue arm -> M4"),
    ("PLSG", 411, 411, "} else if (isDue) {", "an isDue arm -> M4"),
    ("PLSG", 373, 373, "true", "isInstallmentChargeApplicable is the literal true on the main loop"),
    ("PLSG", 376, 376, "true", "same, penalty side"),
    ("PLSG", 479, 479, "isRecalculatedInterestComponent()",
     "isInstallmentChargeApplicable on the separated path"),
    ("PLSG", 483, 483, "isRecalculatedInterestComponent()", "same, penalty side"),
    ("LSP", 533, 535, "instalmentNumber", "isFirstPeriod() is the mutable counter"),
    ("LC", 371, 373, "isInPeriod", "LoanCharge.isDueInPeriod delegates to M1's predicate"),
    ("LRSPW", 251, 254, "isInPeriod", "the shared predicate function"),
    ("PLSG", 140, 140, "applyChargesForCurrentPeriod", "runs BEFORE incrementInstalmentNumber"),
    ("PLSG", 143, 143, "incrementInstalmentNumber()", "the increment"),
    ("PLSG", 154, 154, "updatePeriodsWithCharges", "the separated path, AFTER the loop"),
    # ---- P1-T43-2 : the ambient sites
    ("MONEY", 103, 103, "MoneyHelper.getMathContext()", "two-arg Money.of(CurrencyData,..)"),
    ("MONEY", 115, 115, "MoneyHelper.getMathContext()", "two-arg Money.of(MonetaryCurrency,..)"),
    ("MONEY", 119, 119, "MoneyHelper.getMathContext()", "Money.zero(MonetaryCurrency)"),
    ("MONEY", 130, 132, "MoneyHelper.getMathContext()",
     "Money.zero(CurrencyData) -- OMITTED BY REVISION 8"),
    ("MONEY", 154, 154, "MoneyHelper.getRoundingMode()", "static roundToMultiplesOf(BigDecimal,..)"),
    ("MONEY", 160, 160, "MoneyHelper.getMathContext()", "static roundToMultiplesOf(Money,..)"),
    ("MONEY", 169, 169, "Money.of(existingVal.getCurrencyData(), amountScaled)",
     "three-arg return path routes through the two-arg Money.of"),
    ("MONEY", 224, 234, "Money.of(getCurrencyData(), total)",
     "plus(Iterable) -- OMITTED BY REVISION 8"),
    ("MONEY", 261, 267, "Money.of(getCurrencyData(), newAmount)",
     "plus(double) -- OMITTED BY REVISION 8"),
    ("MONEY", 377, 377, "Money.of(getCurrencyData(), newAmount)", "multipliedBy(double)"),
    ("MONEY", 494, 496, "mc != null ? mc : MoneyHelper.getMathContext()", "getMc()"),
    ("MONEY", 50, 50, "roundToMultiplesOf(amountScaled, currency.getInMultiplesOf())",
     "the site handed a context that ignores it (T42)"),
    ("MONEY", 48, 51, "getDecimalPlaces() == 0", "its guard"),
    ("MONEY", 52, 52, "setScale", "the currency-scale rounding"),
    ("MONEY", 32, 32, "MathContext", "Money's own mc field"),
    ("MH", 35, 35, "PRECISION = 19", "the compile-time precision"),
    ("MH", 91, 93, "new MathContext(PRECISION", "getMathContext()"),
    ("MH", 74, 82, "IllegalStateException", "the uninitialised-tenant throw"),
    ("EMI", 182, 182, "Money.zero(loanProductRelatedDetail.getCurrencyData())",
     "the ONE-ARG overload -> Money.java:130-132, reached on the Path-A call graph"),
    ("EMI", 142, 144, "isAllowFullTermForTranche()", "the PIN that excludes it, not a 3.1 predicate"),
    ("EMI", 155, 174, "addFullTermTrancheDisbursement", "the only caller of buildLoanApplicationTerms"),
    # ---- inherited, highest-value
    ("EMI", 1404, 1413, "calculatePeriodRatio", "the interest call site's multiplier"),
    ("EMI", 1413, 1413, "BigDecimal.valueOf(30)", "the hard-coded days-in-month there"),
    ("EMI", 1508, 1508, "isDaysInMonth_30()", "daysInMonth's ternary"),
    ("EMI", 1536, 1537, "repaymentEvery", "the recurrence call site's multiplier"),
    ("EMI", 1426, 1436, "getDayOfMonth", "the month-end special case"),
    ("EMI", 1432, 1432, "targetDateDay", "its predicate"),
    ("EMI", 1433, 1433, "plusDays(1)", "its effect"),
    ("EMI", 1435, 1435, "getExactDifference", "the whole-months call"),
    ("EMI", 1453, 1453, "divide", "the only MathContext-rounded step of the walk"),
    ("EMI", 1454, 1454, "add", "the exact addition"),
    ("EMI", 1462, 1462, "getStartDate()", "calculateSeedDate reads the SCHEDULE START"),
    ("PLSG", 307, 308, "isBefore(periodDueDate)", "M3, due-EXCLUSIVE"),
    ("PLSG", 132, 132, "setOutstandingLoanBalance", "the row's balance, written in its own iteration"),
    ("PLSG", 351, 351, "addDisbursement", "the registration, in M3's owner period"),
    ("PLSG", 157, 157, "totalOutstanding = BigDecimal.ZERO", "the literal zero"),
]


def main():
    head = subprocess.run(["git", "-C", FIN, "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    print("T45 CITATION CONTENT CHECK - does each load-bearing cited line SAY what it is cited for?")
    print(f"pinned checkout: {FIN} @ {head}")
    print()
    cache = {}
    bad = 0
    for key, lo, hi, token, why in ASSERTIONS:
        path = os.path.join(FIN, F[key])
        if path not in cache:
            cache[path] = open(path).read().split("\n")
        lines = cache[path]
        chunk = "\n".join(lines[lo - 1:hi])
        ok = token in chunk
        if not ok:
            bad += 1
        name = os.path.basename(F[key])
        rng = f"{lo}" if lo == hi else f"{lo}-{hi}"
        print(f"[{'OK  ' if ok else 'FAIL'}] {name}:{rng:<10} contains {token!r}")
        print(f"          claim: {why}")
        if not ok:
            print(f"          ACTUAL: {chunk[:300]!r}")
    print()
    print(f"assertions: {len(ASSERTIONS)}   passed: {len(ASSERTIONS) - bad}   FAILED: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
