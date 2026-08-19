#!/usr/bin/env python3
"""T47 - CONTENT check on the load-bearing citations of DEC-1 revision 10.

The range check (t45_citecheck.py) proves a cited line EXISTS. It does not prove the line
says what the sentence above it claims -- and P1-T43-1 was a citation that existed, was
correctly formatted, and said the opposite of what it was cited for. So this probe asserts,
for every citation revision 9 or revision 10 touches, plus the highest-value ones they inherit, that the
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
    "MATHUTIL": "fineract-core/src/main/java/org/apache/fineract/infrastructure/core/service/MathUtil.java",
    "LSGSI": "fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanScheduleGeneratorServiceImpl.java",
    "LAT": "fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/LoanApplicationTerms.java",
    "LDPH": "fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanDownPaymentHandlerServiceImpl.java",
    "LWPS": "fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java",
    "DU": "fineract-core/src/main/java/org/apache/fineract/infrastructure/core/service/DateUtils.java",
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
    # ================= REVISION 10 =================
    # --- finding 1: the month-end pair, and the YEARS arm that closes the escape route
    ("EMI", 1432, 1432, "targetDateLastDay == targetDateDay && seedDateDay > targetDateDay",
     "rev10 §4.1.1 step B: the closed form's right-hand side is VERBATIM this predicate"),
    ("EMI", 1433, 1433, "repaymentPeriod.getFromDate().plusDays(1)",
     "rev10: when it fires the oracle measures to FromDate.plusDays(1)"),
    ("EMI", 1435, 1435, "DateUtils.getExactDifference(seedDate, repaymentPeriod.getFromDate()",
     "rev10 PINS this as the normative whole-months reading (packed)"),
    ("DU", 308, 317, "unit.between",
     "getExactDifference is ChronoUnit.<unit>.between"),
    ("EMI", 1405, 1405, "ChronoUnit.YEARS",
     "rev10 §4.1.1 step B (iii): the YEARS ratio is computed here"),
    ("EMI", 1598, 1610, "calculateRateFactorPerPeriodBasedOnRepaymentFrequency",
     "rev10: the switch the YEARS ratio is handed to"),
    ("EMI", 1609, 1609, 'throw new UnsupportedOperationException("Invalid repayment frequency")',
     "rev10: the YEARS arm is UNREACHABLE -- this is why T46-YR-A/B throw"),
    ("EMI", 1602, 1608, "case MONTHS ->",
     "rev10: the switch carries DAYS, WEEKS and MONTHS arms and no YEARS arm"),
    ("EMI", 1477, 1480, "repaymentPeriod.getFromDate()",
     "rev10: calculateSeedDate falls back to the period's own FromDate"),

    # --- finding 2: installmentAmountInMultiplesOf is lost BY CALLER
    ("LAT", 579, 606, "assembleFrom(LoanRepaymentScheduleModelData modelData, MathContext mc)",
     "rev10 §2.2: the assembler the seam and LoanScheduleGeneratorServiceImpl share"),
    ("LSGSI", 44, 44, "MathContext mc = MoneyHelper.getMathContext()",
     "rev10 §2.2 per-caller table: this caller reads the AMBIENT context"),
    ("LSGSI", 56, 56, "getInstallmentAmountInMultiplesOf()",
     "rev10 §2.2: the value IS put into the model data ..."),
    ("LSGSI", 63, 63, "scheduleGenerator.generate(mc, modelData)",
     "... and IS carried to generate(), and is then dropped by the assembler"),
    ("LAT", 217, 217, "installmentAmountInMultiplesOf",
     "the field exists on LoanApplicationTerms"),

    # --- finding 3: N46-1, the ambient charge rounding mode
    ("PLSG", 445, 446, "Money.of(cumulative.getCurrency(),",
     "rev10 §4.5.1: the TWO-argument Money.of on the instalment-charge path"),
    ("PLSG", 445, 446, "divide(BigDecimal.valueOf(100), mc)",
     "rev10 §4.5.1: the percentage division DOES carry the threaded mc"),
    ("PLSG", 464, 465, "Money.of(cumulative.getCurrency(),",
     "rev10 §4.5.1: the same two-argument construction on the specified-due-date arm"),
    ("MONEY", 114, 116, "MoneyHelper.getMathContext()",
     "rev10: the two-argument Money.of(MonetaryCurrency, BigDecimal) is AMBIENT"),
    ("MONEY", 52, 52, "setScale(currency.getDecimalPlaces(), getMc().getRoundingMode())",
     "rev10's per-construction rule: the scale-2 rounding point"),
    ("MONEY", 494, 496, "return mc != null ? mc : MoneyHelper.getMathContext()",
     "rev10's per-construction rule: getMc()'s null branch"),
    ("MONEY", 40, 42, "this.mc = mc",
     "rev10's per-construction rule: the instance mc is what the constructing call passed"),
    ("MONEY", 48, 51, "getDecimalPlaces() == 0",
     "rev10 §4.5.1: the gate the inMultiplesOf leak has and the charge leak does NOT"),
    ("MATHUTIL", 472, 473, "new MathContext(precision, MoneyHelper.getRoundingMode())",
     "rev10 §4.1.2, T46-N1: percentageOf(…, int) takes the AMBIENT mode"),
    ("ACLSG", 1897, 1897, "MathUtil.percentageOf(", "T46-N1 site 1 of 6, literal 19"),
    ("ACLSG", 2060, 2060, "MathUtil.percentageOf(", "T46-N1 site 2 of 6, literal 19"),
    ("LAT", 866, 866, "MathUtil.percentageOf(", "T46-N1 site 3 of 6, literal 19"),
    ("LDPH", 198, 198, "MathUtil.percentageOf(", "T46-N1 site 4 of 6, literal 19"),
    ("LWPS", 448, 448, "MathUtil.percentageOf(", "T46-N1 site 5 of 6, literal 19"),
    ("LWPS", 3538, 3538, "MathUtil.percentageOf(", "T46-N1 site 6 of 6, literal 19"),
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
