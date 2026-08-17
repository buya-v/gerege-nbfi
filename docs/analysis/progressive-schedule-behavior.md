# Progressive Loan Schedule Generator — Behavior Analysis

**Scope of this document.** The arithmetic of `EmbeddableProgressiveLoanScheduleGenerator` and its immediate
dependency chain (`ProgressiveLoanScheduleGenerator` → `ProgressiveEMICalculator` → `RepaymentPeriod` /
`InterestPeriod` → `Money` / `MoneyHelper`), as implemented at the pinned Fineract checkout
`/Users/buv/fineract`, commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`. GL/accounting posting, COB, charges/
rates/tax, provisioning, and any cutover plan are explicitly out of scope (see Backlog at the end).

Every material claim below is tagged `[VERIFIED: /absolute/path:LINE]` against source actually read in this
checkout, or `[UNVERIFIED: reason]` where it could not be traced. Several of the core money-path formulas (EMI,
rate factor, per-period interest/principal split for periods 1–3) were independently re-derived by hand against
`EmbeddableProgressiveLoanScheduleGeneratorTest.testGenerate()`'s golden expected values and matched to the cent
— see §9.

---

## 1. Inputs

The embeddable entry point signature is:

```java
public LoanSchedulePlan generate(final MathContext mc, final LoanRepaymentScheduleModelData modelData)
```
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java:45-47]`

### 1.1 The `MathContext mc` parameter

Caller-supplied, not defaulted inside the embeddable wrapper. The CI smoke test and the unit test both use
`new MathContext(12, RoundingMode.HALF_UP)`.
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/misc/Main.java:42]`,
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/test/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGeneratorTest.java:44]`

In the full hosted Fineract application, the same-shaped `MathContext` is instead sourced from
`MoneyHelper.getMathContext()`, which is `new MathContext(19, <tenant RoundingMode>)`
`[VERIFIED: /Users/buv/fineract/fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/MoneyHelper.java:35,91-94]`.
**The embeddable generator is precision-and-rounding-mode agnostic — whatever `MathContext` the caller passes
propagates through the entire calculation** (see §5).

### 1.2 `LoanRepaymentScheduleModelData` fields

Record definition, 19 fields, no field-level javadoc (meaning below is inferred from field name, type, and
downstream usage in `LoanApplicationTerms.assembleFrom`):

`[VERIFIED: /Users/buv/fineract/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/LoanRepaymentScheduleModelData.java:32-39]`

| # | Field | Java type | Meaning / unit |
|---|---|---|---|
| 1 | `scheduleGenerationStartDate` | `LocalDate` | Schedule-generation start date; falls back for `repaymentsStartingFromDate`/`submittedOnDate`-equivalent. |
| 2 | `currency` | `CurrencyData` | Currency code, display symbol, `decimalPlaces`, optional `inMultiplesOf`. |
| 3 | `disbursementAmount` | `BigDecimal` | Principal disbursed, in the currency's **major unit `BigDecimal` representation** (NOT integer minor units — see §9 Go-port hazards). |
| 4 | `disbursementDate` | `LocalDate` | Date of the single disbursement this model supports. |
| 5 | `numberOfRepayments` | `int` | Count of repayment installments (loan term length in periods). |
| 6 | `repaymentFrequency` | `int` | "Repayment every N" step multiplier (`repaymentEvery`). |
| 7 | `repaymentFrequencyType` | `String` | Parsed via `PeriodFrequencyType.valueOf(...)` — e.g. `"MONTHS"`, `"WEEKS"`, `"DAYS"`, `"YEARS"`. Also used as the interest-rate period-frequency type. |
| 8 | `annualNominalInterestRate` | `BigDecimal` | Nominal annual interest rate as a **percentage number** (e.g. `7.0` means 7%), divided by 100 inside the rate-factor formula. |
| 9 | `downPaymentEnabled` | `boolean` | Whether a down-payment period is generated at disbursement. |
| 10 | `daysInMonth` | `DaysInMonthType` | Day-count convention for "days in a month" (`ACTUAL` or `DAYS_30`). |
| 11 | `daysInYear` | `DaysInYearType` | Day-count convention for "days in a year" (`ACTUAL`, `DAYS_360`, `DAYS_364`, `DAYS_365`). |
| 12 | `downPaymentPercentage` | `BigDecimal` (nullable) | Percentage of disbursed amount taken as a down payment. |
| 13 | `installmentAmountInMultiplesOf` | `Integer` (nullable) | Round EMI (and down payment) to the nearest multiple of this integer. |
| 14 | `fixedLength` | `Integer` (nullable, days) | Overrides/forces total loan term length in days. |
| 15 | `interestRecognitionOnDisbursementDate` | `Boolean` (`@NotNull`) | Whether interest accrues starting the disbursement date itself vs. the following day. |
| 16 | `daysInYearCustomStrategy` | `DaysInYearCustomStrategyType` (`@Nullable`) | Overrides leap-year (Feb-29) day-count handling; only meaningful when `daysInYear == ACTUAL`. |
| 17 | `interestMethod` | `InterestMethod` | `FLAT` or `DECLINING_BALANCE` — selects the entire EMI/rate-factor code path (§2). |
| 18 | `allowPartialPeriodInterestCalculation` | `boolean` | Whether interest may be computed for a sub-period rather than only whole repayment periods. |
| 19 | `allowFullTermForTranche` | `boolean` | Governs tranche re-amortization; **dead for the embeddable single-disbursement path** — see §7.2. |

Money-unit note: `disbursementAmount` and `annualNominalInterestRate` are `BigDecimal`, not integer minor units.
This is a first-class Go-port hazard — see §9.

---

## 2. EMI derivation

### 2.1 Call chain from the embeddable entry point

`EmbeddableProgressiveLoanScheduleGenerator.generate(mc, modelData)` →
`ProgressiveLoanScheduleGenerator.generate(mc, modelData)`
`[VERIFIED: .../ProgressiveLoanScheduleGenerator.java:81-84]` (builds `LoanApplicationTerms.assembleFrom(modelData, mc)`
then calls the full `generate(mc, loanApplicationTerms, null, null)` overload) →
main period loop `[VERIFIED: .../ProgressiveLoanScheduleGenerator.java:87-165]` → per-disbursement
`emiCalculator.addDisbursement(...)` `[VERIFIED: .../ProgressiveEMICalculator.java:126-153]` →
`calculateEMIValueAndRateFactors` → `calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod`
`[VERIFIED: .../ProgressiveEMICalculator.java:718-751]` → `calculateEMIOnActualModel` (dispatcher)
`[VERIFIED: .../ProgressiveEMICalculator.java:1674-1683]` →
`calculateEMIOnActualModelWithDecliningBalanceInterestMethod`
`[VERIFIED: .../ProgressiveEMICalculator.java:1722-1742]`.

### 2.2 The EMI formula, exactly as implemented

```java
private void calculateEMIOnActualModelWithDecliningBalanceInterestMethod(List<RepaymentPeriod> repaymentPeriods,
        ProgressiveLoanInterestScheduleModel scheduleModel) {
    final MathContext mc = scheduleModel.mc();
    final BigDecimal rateFactorN = MathUtil.stripTrailingZeros(calculateRateFactorPlus1NForEmi(repaymentPeriods, scheduleModel, mc));
    final BigDecimal fnResult = MathUtil.stripTrailingZeros(calculateFnResultForEmi(repaymentPeriods, scheduleModel, mc));
    final RepaymentPeriod startPeriod = repaymentPeriods.getFirst();
    final Money outstandingBalance = startPeriod.getInitialBalanceForEmiRecalculation();
    final Money equalMonthlyInstallment = Money
            .of(outstandingBalance.getCurrencyData(), calculateEMIValue(rateFactorN, outstandingBalance.getAmount(), fnResult, mc), mc)
            .add(calculateEMIValueForFixedInterest(repaymentPeriods, mc));
    final Money finalEqualMonthlyInstallment = applyInstallmentAmountInMultiplesOf(scheduleModel, equalMonthlyInstallment);
    ...
}
```
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculator.java:1722-1734]`

```java
private BigDecimal calculateEMIValue(final BigDecimal rateFactorPlus1N, final BigDecimal outstandingBalanceForRest,
        final BigDecimal fnResult, MathContext mc) {
    return rateFactorPlus1N.multiply(outstandingBalanceForRest, mc).divide(fnResult, mc);
}
```
`[VERIFIED: ProgressiveEMICalculator.java:1838-1841]`

i.e. **`EMI = rateFactorPlus1N × outstandingBalance / fnResult`**, plus a separately additive fixed-interest
component (`calculateEMIValueForFixedInterest`, an averaged fixed-interest add-on not relevant to the plain
declining-balance case — `[VERIFIED: ProgressiveEMICalculator.java:1846-1849]`).

Where, letting `r_i = 1 + rateFactor_i` be the per-repayment-period "rate factor plus 1" (N periods total):

- **`rateFactorPlus1N` = Π(r_i)** for all N periods:
```java
private BigDecimal calculateRateFactorPlus1NForEmi(final List<RepaymentPeriod> periods, ...) {
    return periods.stream().map(period -> getRateFactorPlus1ForEmi(period, scheduleModel)).reduce(BigDecimal.ONE,
            (BigDecimal acc, BigDecimal value) -> acc.multiply(value, mc));
}
```
`[VERIFIED: ProgressiveEMICalculator.java:1816-1820]`

- **`fnResult` = recursively-built `fn_N`**, seeded at `fn_1=1`, `fn_k = 1 + fn_{k-1} × r_k` for `k=2..N`
  (the `.skip(1)` below is what makes `fn_1=1` the seed rather than the first period's rate factor):
```java
private BigDecimal calculateFnResultForEmi(final List<RepaymentPeriod> periods, ...) {
    return periods.stream().skip(1).map(period -> getRateFactorPlus1ForEmi(period, scheduleModel))
            .reduce(BigDecimal.ONE, (previousFnValue, currentRateFactor) -> fnValue(previousFnValue, currentRateFactor, mc));
}
/** fn = 1 + fnValueFrom * rateFactorEnd */
BigDecimal fnValue(final BigDecimal previousFnValue, final BigDecimal currentRateFactor, final MathContext mc) {
    return BigDecimal.ONE.add(previousFnValue.multiply(currentRateFactor, mc), mc);
}
```
`[VERIFIED: ProgressiveEMICalculator.java:1822-1828, 1982-1993]`

This is algebraically the standard amortization formula `P·i(1+i)^N / ((1+i)^N − 1)` generalized to
per-period-varying rate factors (it reduces to that identity when all `r_i` are equal, via the geometric-series
identity `Σr^k = (r^N−1)/(r−1)`, but **the code never computes the denominator that way** — it always uses the
`fn` recurrence, which is what a Go port must replicate bit-for-bit, not the closed-form geometric sum, to avoid
drift under time-varying rates, interest-rate changes, or interest-pause periods).

`getRateFactorPlus1ForEmi` substitutes `1` (i.e. a zero-rate factor) for any period flagged
`isInterestPaymentGrace()` when `scheduleModel.isInterestPauseForEmiCalculationEnabled()`:
`[VERIFIED: ProgressiveEMICalculator.java:1830-1833]`.

`RepaymentPeriod.getRateFactorPlus1()` = `1 + Σ(InterestPeriod.rateFactor)` across all interest sub-periods
inside that repayment period (usually exactly one interest period per repayment period in the simple
non-reschedule case):
```java
private BigDecimal calculateRateFactorPlus1() {
    return interestPeriods.stream().map(InterestPeriod::getRateFactor).reduce(BigDecimal.ONE, BigDecimal::add);
}
```
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/data/RepaymentPeriod.java:209-218]`
— note the `+1` is the `BigDecimal.ONE` reduce-seed here, not literally added inside the per-leaf rate-factor
helper (the method-level javadoc on the leaf helpers, e.g. line 1933-1934, is misleading on this point — the
leaf itself returns the bare interest fraction, not `1+fraction`; confirm by reading `rateFactorByRepaymentPeriod`
in §3, which returns only the multiplicative term).

### 2.3 Rate-per-period conversion — from annual percentage to per-period fraction

```java
private BigDecimal calcNominalInterestRatePercentage(final BigDecimal interestRate, MathContext mc) {
    return MathUtil.nullToZero(interestRate).divide(DIVISOR_100, mc);
}
```
`[VERIFIED: ProgressiveEMICalculator.java:1318-1320]`, `DIVISOR_100 = new BigDecimal("100")`
`[VERIFIED: ProgressiveEMICalculator.java:75]`

This only converts percentage → fraction (`7.0 → 0.07`); it does **not** divide by periods-per-year. The
periods-per-year reduction happens entirely inside the day-count-driven rate-factor formula (§3), via the
`daysInYear` divisor.

### 2.4 `MathContext` in force at each step

Every method above re-derives `MathContext mc = scheduleModel.mc();` at its own top
(`[VERIFIED: ProgressiveEMICalculator.java:1724]` for the EMI method itself, and similarly at lines 1357, 1488,
1616, 1649, 1189, 1260 for the other methods discussed in this document) — `scheduleModel.mc()` is the **single
`MathContext` object passed by the caller into `EmbeddableProgressiveLoanScheduleGenerator.generate(mc, ...)`**,
stored as a `private final MathContext mc;` field on `ProgressiveLoanInterestScheduleModel`
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/data/ProgressiveLoanInterestScheduleModel.java:65,75-92]`.
No `new MathContext(...)` literal exists anywhere inside `ProgressiveEMICalculator.java` (confirmed by grep — zero
hits). **All `BigDecimal.multiply(..., mc)` / `.divide(..., mc)` calls in the rate-factor and EMI chain use the
exact same caller-supplied `MathContext`** — e.g. 12 significant digits, `HALF_UP`, in the golden test.

---

## 3. Per-period interest/principal split

### 3.1 Two distinct rate factors are computed per interest period, for two different purposes

`calculateRateFactorForRepaymentPeriod` sets both on every `InterestPeriod`:
```java
public void calculateRateFactorForRepaymentPeriod(final RepaymentPeriod repaymentPeriod, final ProgressiveLoanInterestScheduleModel scheduleModel) {
    repaymentPeriod.getInterestPeriods().forEach(interestPeriod -> {
        interestPeriod.setRateFactor(calculateRateFactorPerPeriod(scheduleModel, repaymentPeriod, interestPeriod.getFromDate(), interestPeriod.getDueDate()));
        interestPeriod.setRateFactorTillPeriodDueDate(calculateRateFactorPerPeriodForInterest(scheduleModel, repaymentPeriod, interestPeriod.getFromDate(), repaymentPeriod.getDueDate()));
    });
}
```
`[VERIFIED: ProgressiveEMICalculator.java:636-644]`

- `rateFactor` (from `calculateRateFactorPerPeriod`, `[VERIFIED: ProgressiveEMICalculator.java:1486-1540]`) feeds
  the **compounding EMI product** in §2.2.
- `rateFactorTillPeriodDueDate` (from `calculateRateFactorPerPeriodForInterest`,
  `[VERIFIED: ProgressiveEMICalculator.java:1355-1417]`) feeds the **actual booked interest** for the sub-period,
  below. Structurally near-identical (same day-count dispatch tree, §4), but note it is a genuinely separate call
  with its own dispatch, not a cached re-use of `rateFactor`.

### 3.2 Interest for a sub-period, from outstanding balance

```java
public BigDecimal getCalculatedDueInterest(InterestMethod method, long lengthTillPeriodDueDate) {
    if (lengthTillPeriodDueDate == 0) { return BigDecimal.ZERO; }
    BigDecimal baseAmount = switch (method) {
        case FLAT -> getRepaymentPeriod().calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod(this).getAmount();
        case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount();
        default -> throw new UnsupportedOperationException("Method not implemented: " + method);
    };
    return baseAmount
            .multiply(getRateFactorTillPeriodDueDate(), getMc())
            .divide(BigDecimal.valueOf(lengthTillPeriodDueDate), getMc())
            .multiply(BigDecimal.valueOf(getLength()), getMc());
}
```
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/data/InterestPeriod.java:145-158]`

i.e. for `DECLINING_BALANCE`:

**`interest_subperiod = outstandingLoanBalance × rateFactorTillPeriodDueDate / lengthTillPeriodDueDate × length(this sub-period)`**

`getLength()` = `ChronoUnit.DAYS.between(fromDate, dueDate)` of the interest sub-period
`[VERIFIED: InterestPeriod.java:160-162]`; `getLengthTillPeriodDueDate()` = days from the sub-period's `fromDate`
to the *repayment period's* `dueDate` `[VERIFIED: InterestPeriod.java:164-166]`. In the common case (one interest
period per repayment period, no mid-period disbursement/rate-change split) `length == lengthTillPeriodDueDate`, so
the ratio collapses to `1` and `interest = outstandingBalance × rateFactorTillPeriodDueDate` exactly.

Outstanding balance roll-forward for a `DECLINING_BALANCE` interest sub-period (`updateOutstandingLoanBalance`):
for the **first** interest period of a repayment period, it pulls forward the previous repayment period's closing
balance, adjusted for disbursement/capitalized-income/balance-correction, **minus that previous period's due
principal plus its paid principal** (i.e. principal reduction only happens once, at the repayment-period
boundary):
```java
this.outstandingLoanBalance = MathUtil.negativeToZero(previousInterestPeriod.getOutstandingLoanBalance()
        .plus(previousInterestPeriod.getDisbursementAmount(), getMc())
        .plus(previousInterestPeriod.getCapitalizedIncomePrincipal(), getMc())
        .plus(previousInterestPeriod.getBalanceCorrectionAmount(), getMc())
        .minus(previousRepaymentPeriod.get().getDuePrincipal(), getMc())
        .plus(previousRepaymentPeriod.get().getPaidPrincipal(), getMc()), getMc());
```
`[VERIFIED: InterestPeriod.java:168-179]` (non-first-interest-period branch at lines 180-187 omits the
principal-reduction term, since it only applies at the repayment-period boundary).

### 3.3 Principal for the period — order of operations: EMI and interest come first, principal is the remainder

```java
public Money getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest() {
    return getEmi().plus(getTotalCreditedAmount(), mc).plus(getFutureUnrecognizedInterest(), getMc());
}
public Money getDuePrincipal() {
    return MathUtil.max(MathUtil.negativeToZero(getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().minus(getDueInterest(), getMc()), getMc()),
            getPaidPrincipal(), false);
}
```
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/data/RepaymentPeriod.java:293-296, 345-350]`

**`duePrincipal = max(EMI + creditedAmounts + futureUnrecognizedInterest − dueInterest, alreadyPaidPrincipal)`**,
floored at zero before the `max`. In the plain no-credits, no-unrecognized-interest, nothing-paid-yet case this is
simply **`principal = EMI − interest`**, computed strictly *after* EMI (§2) and interest (§3.2) are both already
known — principal is never computed independently; it is always the balancing remainder of a fixed EMI.

**Order of operations per repayment period, precisely:**
1. Compute `rateFactor` and `rateFactorTillPeriodDueDate` for every interest sub-period (§3.1, day-count math, §4).
2. Compute EMI once for the whole schedule (or the "related periods" set on a recalculation event) from the
   compounding rate-factor product (§2.2) — a single value, held constant across ordinary periods.
3. Compute each period's `dueInterest` (= `getCalculatedDueInterest()`, §3.2) from the **outstanding balance
   rolled forward from the previous period's principal reduction** (§3.2).
4. Derive `duePrincipal = EMI − dueInterest` (floored, credit-adjusted) — §3.3.
5. Roll the outstanding balance forward for the next period using this period's `duePrincipal` (§3.2).
6. The **last** unpaid period is separately re-adjusted to absorb the running residual so principal totals
   reconcile exactly (§6).

---

## 4. Day-count convention

**Traced conclusion: this is a fixed 30/360 (30-day month, 360-day year) convention under the default
configuration (`DaysInMonthType.DAYS_30` + `DaysInYearType.DAYS_360`), NOT actual/actual and NOT a
"always-compute-real-calendar-days" scheme** — with an important caveat: it is configurable per loan, and an
`ACTUAL`/`ACTUAL` alternative path exists in the same code, used only when the enum values are set to `ACTUAL`.

### 4.1 The enums are literal constants, not computed lengths, unless `ACTUAL`

```java
public enum DaysInYearType {
    INVALID(0, ...), ACTUAL(1, ...), DAYS_360(360, ...), DAYS_364(364, ...), DAYS_365(365, ...);
    ...
    public Integer getNumberOfDays(final LocalDate referenceDate) {
        return this == ACTUAL ? referenceDate.lengthOfYear() : this.getValue();
    }
}
```
`[VERIFIED: /Users/buv/fineract/fineract-core/src/main/java/org/apache/fineract/portfolio/common/domain/DaysInYearType.java:36-40, 81-86]`

```java
public enum DaysInMonthType {
    INVALID(0, ...), ACTUAL(1, ...), DAYS_30(30, ...);
    ...
    public Integer getNumberOfDays(final LocalDate referenceDate) {
        return this == ACTUAL ? referenceDate.lengthOfMonth() : this.getValue();
    }
}
```
`[VERIFIED: /Users/buv/fineract/fineract-core/src/main/java/org/apache/fineract/portfolio/common/domain/DaysInMonthType.java:34-36, 75-80]`

So `DAYS_360.getNumberOfDays(anyDate) == 360` and `DAYS_30.getNumberOfDays(anyDate) == 30` **always**, regardless
of the actual calendar — these are compile-time constants selected by a runtime `switch`, never computed from
`LocalDate`. Only `ACTUAL` computes `referenceDate.lengthOfYear()` (365/366) or `referenceDate.lengthOfMonth()`
(28–31).

The default config used by the shipped test and CI smoke-test is exactly `DAYS_30` + `DAYS_360`
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/misc/Main.java:56-57]`,
`[VERIFIED: .../EmbeddableProgressiveLoanScheduleGeneratorTest.java:58-59]`.

### 4.2 How the period fraction is actually assembled (`DAYS_30`/`DAYS_360` path)

Dispatch (for `MONTHS` frequency, `DAYS_30`, no partial-period split):
`calculateRateFactorPerPeriodForInterest` → not the "same-as-repayment-period" shortcut unless
`interestCalculationPeriodMethod.isSameAsRepaymentPeriod()` is set (not the case for the embeddable path's
default) → `daysInMonthType.isDaysInMonth_30()` branch → computes a `periodRatio` per `ChronoUnit.MONTHS` via
`calculatePeriodRatio` (equals `repaymentEvery`, i.e. `1`, when the interest sub-period exactly spans one whole
repayment period) → `calculateRateFactorPerPeriodBasedOnRepaymentFrequency(..., periodRatio, daysInMonth=30,
daysInYear=360, ...)` → `MONTHS` case → `rateFactorByRepaymentEveryMonth(interestRate, repaymentEvery=periodRatio,
daysInMonth=30, daysInYear=360, actualDaysInPeriod, calculatedDaysInPeriod, mc)`
`[VERIFIED: ProgressiveEMICalculator.java:1400-1414, 1598-1611, 1922-1927]` → bottoms out in the shared leaf:

```java
private BigDecimal rateFactorByRepaymentPeriod(final BigDecimal interestRate, final BigDecimal repaymentPeriodMultiplierInDays,
        final BigDecimal repaymentEvery, final BigDecimal daysInYear, final BigDecimal actualDaysInPeriod,
        final BigDecimal calculatedDaysInPeriod, final MathContext mc) {
    if (MathUtil.isZero(calculatedDaysInPeriod)) { return BigDecimal.ZERO; }
    final BigDecimal interestFractionPerPeriod = repaymentPeriodMultiplierInDays.multiply(repaymentEvery, mc).divide(daysInYear, mc);
    return interestRate.multiply(interestFractionPerPeriod, mc).multiply(actualDaysInPeriod, mc)
            .divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode());
}
```
`[VERIFIED: ProgressiveEMICalculator.java:1950-1963]`

So, in full:

**`rateFactor = interestRate × (30 × repaymentEvery / 360) × actualDaysInPeriod / calculatedDaysInPeriod`**

`actualDaysInPeriod` = `ChronoUnit.DAYS.between(interestPeriodFromDate, interestPeriodDueDate)` (real calendar
days of the sub-period) `[VERIFIED: ProgressiveEMICalculator.java:1500-1501]`,
`calculatedDaysInPeriod` = `ChronoUnit.DAYS.between(repaymentPeriod.fromDate, repaymentPeriod.dueDate)` (real
calendar days of the whole repayment period) `[VERIFIED: ProgressiveEMICalculator.java:1502-1503]`, via
`DateUtils.getDifferenceInDays` = `ChronoUnit.DAYS.between(...)`
`[VERIFIED: /Users/buv/fineract/fineract-core/src/main/java/org/apache/fineract/infrastructure/core/service/DateUtils.java:319-321]`.

In the ordinary case where the interest sub-period coincides exactly with the repayment period (no mid-period
disbursement, rate change, or reschedule split), `actualDaysInPeriod == calculatedDaysInPeriod`, so that ratio is
exactly `1` and the **real calendar-day counts cancel out**, leaving the pure fixed 30/360 result:
`interestRate × 30 × repaymentEvery / 360`. Real calendar days only matter as a correction ratio for *partial*
sub-periods (e.g. a disbursement or interest-rate change landing mid-repayment-period) — they never replace the
30/360 constants in the default configuration.

**A February with 28 days, or January with 31 days, is treated identically to any other month under `DAYS_30` —
the calendar length of the specific month is irrelevant** when the sub-period spans a whole repayment period; the
formula always uses the literal constant `30`. This is the classic banking "30/360" convention (specifically the
30-fixed / 360-fixed variant, not 30E/360 or 30/360 US day-adjustment rules — no end-of-month day-shifting logic
was found in `rateFactorByRepaymentPeriod` itself).

### 4.3 The `ACTUAL`/`ACTUAL` alternative (present in code, not the default)

If `DaysInYearType.ACTUAL` is configured, `getNumberOfDays` returns the real `lengthOfYear()` (365 or 366)
`[VERIFIED: DaysInYearType.java:85]`. When the interest sub-period additionally spans a calendar-year boundary
(`numberOfYearsDifferenceInPeriod > 0`), a `partialPeriodCalculationNeeded` flag triggers `calculatePeriodFractions`,
which sums `actualDaysInEachCalendarYearSegment / Year.of(year).length()` per year:
```java
while (actualYear <= endYear) {
    fractionPeriodDueDate = actualYear == endYear ? interestPeriodDueDate : getFractionPeriodDueDateForEndOfYear(scheduleModel, actualYear);
    BigDecimal numberOfDaysInYear = BigDecimal.valueOf(Year.of(actualYear).length());
    BigDecimal calculatedDaysInActualYear = BigDecimal.valueOf(DateUtils.getDifferenceInDays(actualDate, fractionPeriodDueDate));
    cumulatedRateFactor = cumulatedRateFactor.add(calculatedDaysInActualYear.divide(numberOfDaysInYear, mc), mc);
    ...
}
```
`[VERIFIED: ProgressiveEMICalculator.java:1372-1374, 1550-1568]` — a genuine actual/actual computation, but **not**
the path exercised by the default `DAYS_30`/`DAYS_360` config. `DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY`
overrides a computed `366` down to `365`/`366` depending on whether Feb-29 literally falls in the period
`[VERIFIED: ProgressiveEMICalculator.java:1342-1353]`; it is only reachable when `numberOfDays == 366`, which
fixed `DAYS_360` never produces, so it's irrelevant to the default config.

### 4.4 Period-boundary date generation (separate from day-count arithmetic)

`DefaultScheduledDateGenerator.generateRepaymentPeriods` steps `repaymentPeriodNumber` from `1` to
`numberOfRepayments`, each iteration computing the next due date via `startDate.plusMonths/plusWeeks/plusDays/
plusYears(repaidEvery)` dispatched on `PeriodFrequencyType`
`[VERIFIED: /Users/buv/fineract/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/DefaultScheduledDateGenerator.java:50-75, 117-161, 311-333]`
— this uses `java.time.LocalDate`'s native calendar arithmetic (which itself correctly clamps month-end
overflow, e.g. `Jan 31 + 1 month = Feb 28/29`, per `LocalDate.plusMonths` semantics), independent of the
`DaysInMonthType`/`DaysInYearType` day-count convention used for *interest* math above. `fixedLength` can override
the final due date `[VERIFIED: DefaultScheduledDateGenerator.java:61-67]`.

---

## 5. Rounding

### 5.1 Two rounding layers, by construction

1. **Intermediate `BigDecimal` arithmetic** (rate factors, `fn`, `rateFactorPlus1N`, raw EMI value) — every
   `.multiply(..., mc)` / `.divide(..., mc)` in §2–§4 uses the single caller-supplied `MathContext` (precision +
   `RoundingMode` both from that one object) — `[VERIFIED: ProgressiveEMICalculator.java:1950-1963, 1838-1841,
   1816-1828]` and the `.setScale(mc.getPrecision(), mc.getRoundingMode())` redundant clamp at the end of every
   rate-factor leaf `[VERIFIED: ProgressiveEMICalculator.java:1962-1963, 1979-1980]`.
2. **Final currency-scale rounding** — happens exactly once, inside `Money`'s private constructor, whenever a raw
   `BigDecimal` is wrapped into a `Money`:
```java
private Money(final CurrencyData currency, final BigDecimal amount, final MathContext mc) {
    this.currency = currency;
    this.mc = mc;
    final BigDecimal amountZeroed = defaultToZeroIfNull(amount);
    BigDecimal amountScaled = amountZeroed.stripTrailingZeros();
    if (currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0 && currency.getInMultiplesOf() > 0
            && MathUtil.isGreaterThanZero(amountScaled)) {
        amountScaled = roundToMultiplesOf(amountScaled, currency.getInMultiplesOf());
    }
    this.amount = amountScaled.setScale(currency.getDecimalPlaces(), getMc().getRoundingMode());
}
```
`[VERIFIED: /Users/buv/fineract/fineract-core/src/main/java/org/apache/fineract/organisation/monetary/domain/Money.java:40-53]`
— `setScale(currency.getDecimalPlaces(), mc.getRoundingMode())`, i.e. **2 decimal places for MNT (ISO 4217 minor
unit 2) or USD**, using the `RoundingMode` of whichever `MathContext` was passed into that specific `Money.of(...)`
call. In the progressive-loan module, that is overwhelmingly the same threaded `mc` — grep of `Money.of(...)` /
`Money.zero(...)` call sites in `ProgressiveEMICalculator.java` shows the explicit `mc` passed in every
non-trivial (non-always-zero) case `[VERIFIED: e.g. ProgressiveEMICalculator.java:1731-1733]`.

**So: rate-factor and EMI math run at the caller's `MathContext` precision (12 significant digits, `HALF_UP`, in
the golden test) as raw `BigDecimal`s; only when a result is wrapped into `Money` does it get rounded down to the
currency's 2 decimal places, using that same `RoundingMode`.** This is precision-narrowing rounding
(19 or 12 significant digits → 2 decimal places), applied once per `Money.of(...)` call, not a running
double-rounding chain in the common path.

### 5.2 `MoneyHelper` — tenant-scoped, no compiled-in default

```java
public static final int PRECISION = 19;
...
public static RoundingMode getRoundingMode() {
    String tenantId = getTenantIdentifier();
    RoundingMode roundingMode = roundingModeCache.get(tenantId);
    if (roundingMode == null) { throw new IllegalStateException("Rounding mode is not initialized for tenant: " + tenantId); }
    return roundingMode;
}
public static MathContext getMathContext() {
    String tenantId = getTenantIdentifier();
    return mathContextCache.computeIfAbsent(tenantId, k -> new MathContext(PRECISION, getRoundingMode()));
}
```
`[VERIFIED: MoneyHelper.java:35, 74-82, 91-94]` — `RoundingMode` is populated per-tenant at startup via
`initializeTenantRoundingMode(tenantIdentifier, roundingModeValue)` (an int `0-6` mapped to `RoundingMode.valueOf`)
`[VERIFIED: MoneyHelper.java:54-65]` and **is not hard-coded in this class**; calling `getRoundingMode()`/
`getMathContext()` before tenant initialization throws `IllegalStateException`.
`[UNVERIFIED: the actual production default RoundingMode value passed into `initializeTenantRoundingMode` at
platform bootstrap — lives in tenant/DB config outside this module, not traced.]`

**Go-port-relevant consequence:** the embeddable generator is documented as Spring-free
`[VERIFIED: EmbeddableProgressiveLoanScheduleGenerator.java:38-43]`, but there is exactly one path where it still
transitively reaches the tenant-scoped `MoneyHelper` — see §5.3.

### 5.3 `installmentAmountInMultiplesOf` rounding — two call sites, two different `MathContext` sources

- **Down payment** (`ProgressiveLoanScheduleGenerator.java`) uses the **3-arg** `Money.roundToMultiplesOf`
  overload with the explicit threaded `mc`:
  `Money.roundToMultiplesOf(downPaymentAmount, loanApplicationTerms.getInstallmentAmountInMultiplesOf(), mc)`
  `[VERIFIED: ProgressiveLoanScheduleGenerator.java:336-337]`.
- **EMI** (`ProgressiveEMICalculator.java`) uses the **2-arg** overload, which silently falls back to
  `MoneyHelper.getMathContext()` (the tenant-global mode) instead of the model's own `mc`:
```java
private Money safeRoundingForEMI(final Money unRoundedEMI, final Integer multiplesOf) {
    final Money roundedEMI = Money.roundToMultiplesOf(unRoundedEMI, multiplesOf);   // 2-arg → MoneyHelper.getMathContext()
    if (roundedEMI.isZero() && unRoundedEMI.isGreaterThanZero()) { return unRoundedEMI; }
    return roundedEMI;
}
```
`[VERIFIED: ProgressiveEMICalculator.java:1761-1776]`

Both variants of `roundToMultiplesOf` do the same arithmetic — `amountScaled.divide(inMultiplesOfValue, 0,
mc.getRoundingMode()).multiply(inMultiplesOfValue)` — i.e. round to the **nearest** multiple under whatever
`RoundingMode` is in force (not simply "always up" or "always down")
`[VERIFIED: Money.java:150-170]`. The `safeRoundingForEMI` fallback guard means a positive EMI is never rounded
down to zero even if `multiplesOf` exceeds it.

**This is a real parity risk for the Go port and for golden-vector capture:** if `installmentAmountInMultiplesOf`
is set and the embeddable generator is invoked outside an initialized Fineract tenant context, EMI-multiples
rounding throws `IllegalStateException` from `MoneyHelper`. The shipped unit test avoids this entirely by setting
`installmentAmountInMultiplesOf = null`
`[VERIFIED: EmbeddableProgressiveLoanScheduleGeneratorTest.java:60]`. Any golden-vector case that exercises
`installmentAmountInMultiplesOf` must therefore either avoid it, or the oracle-capture harness must initialize a
`MoneyHelper` tenant with a known `RoundingMode` first — otherwise EMI rounding and down-payment rounding could
silently diverge in mode even when both notionally use "the same" `MathContext`.

### 5.4 `CurrencyData.decimalPlaces`

Plain field, `private int decimalPlaces;`
`[VERIFIED: /Users/buv/fineract/fineract-core/src/main/java/org/apache/fineract/organisation/monetary/data/CurrencyData.java:39]`
— `CurrencyData` performs no rounding itself; it is purely a scale carrier consumed by `Money`'s constructor
(§5.1). For MNT this must be `2` (ISO 4217 minor unit 2) when constructing `CurrencyData` for oracle capture.

---

## 6. Final-period balancing

`calculateLastUnpaidRepaymentPeriodEMI` finds the last not-fully-paid repayment period and assigns it the entire
running residual between what should have accumulated (disbursed + capitalized income + credited principal + due
interest) and what the EMI schedule actually totals:

```java
Optional<RepaymentPeriod> findLastUnpaidRepaymentPeriod = scheduleModel.repaymentPeriods().stream()
        .filter(rp -> !rp.isFullyPaid()).reduce((first, second) -> second);
...
Money totalDueInterest = scheduleModel.repaymentPeriods().stream().map(RepaymentPeriod::getDueInterest)
        .reduce(scheduleModel.zero(), (m1, m2) -> m1.plus(m2, mc));
Money totalEMI = scheduleModel.repaymentPeriods().stream()
        .map(RepaymentPeriod::getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest)
        .reduce(scheduleModel.zero(), (m1, m2) -> m1.plus(m2, mc));
Money totalDisbursedAmount = scheduleModel.repaymentPeriods().stream()
        .flatMap(rp -> rp.getInterestPeriods().stream().map(InterestPeriod::getDisbursementAmount))
        .reduce(scheduleModel.zero(), (m1, m2) -> m1.plus(m2, mc));
Money totalCapitalizedIncome = scheduleModel.repaymentPeriods().stream()
        .flatMap(rp -> rp.getInterestPeriods().stream().map(InterestPeriod::getCapitalizedIncomePrincipal))
        .reduce(scheduleModel.zero(), (m1, m2) -> m1.plus(m2, mc));

Money diff = totalDisbursedAmount.plus(totalCapitalizedIncome, mc).plus(scheduleModel.getTotalCreditedPrincipal(), mc)
        .plus(totalDueInterest, mc).minus(totalEMI, mc);

Money adjustedEmi = repaymentPeriod.getEmi().add(diff, mc);
...
repaymentPeriod.setEmi(adjustedEmi);
```
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculator.java:1160-1219]` (the guard clauses around this snippet are at lines
1162-1174, 1178-1181, 1206-1215 — a floor so the adjustment never drops the period's EMI below its already-paid
principal+interest, recursing once if the floor is hit).

**Mechanically: `diff` is a single running-total residual (plain `Money`/`BigDecimal` subtraction of cumulative
sums), and it is added *entirely* onto the last unpaid period's EMI — not redistributed proportionally across
periods.** Since every *other* period's principal is `EMI − interest` (§3.3) and holds the constant EMI computed
in §2.2, only the last unpaid period's EMI moves, which is exactly what forces total principal collected to equal
total principal disbursed (+ capitalized income, credits) to the cent, regardless of BigDecimal rounding drift
accumulated across the earlier periods. This method is invoked after every principal-affecting event
(`addDisbursement`, `addCapitalizedIncome`, `addBalanceCorrection`, `payPrincipal`, etc. — grep shows 9 call sites
in `ProgressiveEMICalculator.java`), always as the last step, so it is the single, unconditional zeroing mechanism
for the whole schedule, not merely a last-period special case invoked only once at generation time.

A related but distinct mechanism, `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`
`[VERIFIED: ProgressiveEMICalculator.java:1258-1309]`, re-levels EMI across a set of not-yet-due periods to keep
them equal after certain events, iterating up to 3 times (`adjustCounter <= 3`, line 1308); it always calls
`calculateLastUnpaidRepaymentPeriodEMI` again afterward (line ~1288 area), so exact zeroing always ultimately
happens in the mechanism quoted above, never in the leveling step itself.

---

## 7. Edge cases

### 7.1 Zero-interest (0% annual nominal rate)

No explicit `if (rate == 0)` / `isZeroInterestRate` branch exists anywhere in `ProgressiveEMICalculator.java`
(confirmed by exhaustive grep of `isZero`/`== 0`/`ZERO)` — every hit is either a `Money.isZero()` amount check or
the unrelated `MathUtil.isZero(calculatedDaysInPeriod)` division-by-zero guard at
`[VERIFIED: ProgressiveEMICalculator.java:1953, 1972]`). Zero interest flows naturally: `calcNominalInterestRatePercentage(0, mc) = 0` `[VERIFIED: ProgressiveEMICalculator.java:1318-1320]`
multiplies out to `rateFactor = 0` in `rateFactorByRepaymentPeriod` (§4.2), so `r_i = 1+0 = 1` for every period,
`rateFactorPlus1N = 1^N = 1`, and `fnResult` reduces to the plain integer period count `N` (since
`fnValue(prev, 1, mc) = 1 + prev·1 = prev+1`, starting at `fn_1=1`, so `fn_N = N`). **EMI collapses to
`outstandingBalance × 1 / N = principal / N`, a pure equal-principal split with zero interest** — algebraically
correct and requires no special-casing, but a Go port must confirm its own `fn` recurrence produces exactly
integer `N` at zero rate (not `N ± rounding noise`) since BigDecimal division/multiply at each recursive step
could in principle introduce drift; the residual-absorption mechanism (§6) would mask any such drift onto the
last period, which is worth an explicit golden-vector row (see §8, `ls-003`/`ls-004`).

### 7.2 Multi-disbursement (tranche)

Tranche machinery exists in `ProgressiveLoanScheduleGenerator`/`ProgressiveEMICalculator`
(`processDisbursements` iterates a `disbursementDataList`
`[VERIFIED: ProgressiveLoanScheduleGenerator.java:294-353]`, a post-loop tranche pass runs when
`isMultiDisburseLoan()` `[VERIFIED: ProgressiveLoanScheduleGenerator.java:147-150]`, and
`addFullTermTrancheDisbursement` re-amortizes over the full remaining term when
`isAllowFullTermForTranche()` `[VERIFIED: ProgressiveEMICalculator.java:142-174]`), but it is **not reachable
from `LoanRepaymentScheduleModelData`**: that record has only single `disbursementAmount`/`disbursementDate`
fields (§1.2, no list), `LoanApplicationTerms.assembleFrom(modelData, mc)` always sets an empty
`disbursementDatas()` list `[VERIFIED: /Users/buv/fineract/fineract-loan/.../LoanApplicationTerms.java:600 — cited
by upstream research agent, not independently re-read in this session]`, and `isMultiDisburseLoan()` defaults to
`false` for any `LoanApplicationTerms` built via the `Builder`-based `assembleFrom(modelData, mc)` path used here
(no setter for it on that `Builder`). **Multi-disbursement is genuinely out of scope for the embeddable
single-disbursement generator** — do not build a golden-vector row for it against this entry point.

### 7.3 Principal that does not divide evenly by the term

No special handling exists beyond the general mechanism in §6: ordinary periods get the constant EMI (§2.2, itself
already a `BigDecimal` division that will not land on an exact 2-decimal-place boundary in general), and the last
unpaid period absorbs whatever residual remains after all `setScale`-rounded `Money` interest/principal splits
across the other periods. This is precisely why §6 exists — it should be exercised explicitly in the vector matrix
with principals chosen to not divide evenly (see `ls-005`, `ls-006`).

### 7.4 Month-end and leap-year disbursement dates

Two independent mechanisms are involved and must both be captured:
- **Date generation**: `DefaultScheduledDateGenerator` uses `LocalDate.plusMonths(...)`-family arithmetic (§4.4),
  which already handles month-end overflow per Java's `LocalDate` semantics (e.g. `2026-01-31 + 1 month` yields
  `2026-02-28`, and further `+1 month` from `2026-02-28` yields `2026-03-28`, **not** `2026-03-31`+ - `LocalDate`
  does not "remember" the original day-of-month once clamped). This drift behavior, not merely "does it handle
  Feb correctly," is exactly what a Go port's date-stepping must replicate bit-for-bit — a naive
  `time.AddDate(0,1,0)` in Go has different month-end clamping semantics than Java's `LocalDate.plusMonths`, so
  this is a first-class golden-vector target (`ls-008`, `ls-009`, `ls-010`).
- **Interest day-count**: under the default `DAYS_30`/`DAYS_360` convention (§4.2), the day-count math is
  insensitive to the actual month length or leap-year status when the interest sub-period exactly spans one
  repayment period — `actualDaysInPeriod`/`calculatedDaysInPeriod` cancel to `1` regardless of whether the period
  crossed Feb 29 or not. **Leap-year and month-end edge cases under `DAYS_30`/`DAYS_360` primarily exercise the
  date-generation mechanism (bullet above), not the interest-fraction formula** — the golden-vector value of these
  rows is mostly to pin down date-stepping parity, plus (secondarily) to confirm the Go port's `DAYS_30`/`DAYS_360`
  path doesn't accidentally leak real calendar-day sensitivity where Fineract has none.

### 7.5 Single-period loans

No `if (numberOfRepayments == 1)` guard exists in `DefaultScheduledDateGenerator.generateRepaymentPeriods`
(loop runs once, and the "last period" branch — which every loan's final period passes through — applies)
`[VERIFIED: DefaultScheduledDateGenerator.java:58-73]`, nor in `ProgressiveLoanScheduleGenerator.generate`'s main
loop (iterates the periods list regardless of size) `[VERIFIED: ProgressiveLoanScheduleGenerator.java:116-145]`.
For a single period, `fnResult = fn_1 = 1` (the `.skip(1)` reduce never executes its combining lambda, staying at
seed `BigDecimal.ONE`) and `rateFactorPlus1N = r_1`, so `EMI = r_1 × principal / 1 = principal × (1+rateFactor)` —
i.e. principal + one period's interest, exactly as expected for a bullet/single-installment loan. `[UNVERIFIED:
absence-of-special-case is a negative claim verified only by grep across the two generator files, not exhaustive
line-by-line reading of unrelated re-age/reschedule sections of `ProgressiveEMICalculator.java` (~700-1300,
~1600-2200), which are not on this call path for the embeddable generator.]`

---

## 8. Vector matrix — oracle-capture cases

All monetary amounts are given as **MNT integer minor units** (minor unit = 2; `1,000,000₮ = 100000000`). Every
row assumes `interestMethod = DECLINING_BALANCE`, `downPaymentEnabled = false`, `allowPartialPeriodInterestCalculation = true`,
`interestRecognitionOnDisbursementDate = false`, `installmentAmountInMultiplesOf = null`, `fixedLength = null`,
`daysInYearCustomStrategy = null`, `allowFullTermForTranche = false` unless a column overrides it. `mc` for
capture should be pinned explicitly (e.g. `MathContext(19, HALF_UP)` to match `MoneyHelper.PRECISION`, or the
project's chosen capture precision — record whichever is used alongside the vectors). Timezone only affects how
the civil disbursement date is derived/displayed upstream of this generator (it consumes a bare `LocalDate`); it
is included here to pin the tz-to-civil-date derivation at the boundary, per the project's no-hardcoded-offset
rule.

| case id | principal (MNT minor units) | annual rate % | periods | freq | disbursement date | tz | daysInMonth | daysInYear | purpose |
|---|---|---|---|---|---|---|---|---|---|
| ls-001-baseline-6m-ulaanbaatar | 100000000 (1,000,000₮) | 24.00 | 6 | MONTHS | 2026-03-02 | Asia/Ulaanbaatar | DAYS_30 | DAYS_360 | Baseline divides-evenly case, primary tz |
| ls-002-baseline-6m-hovd | 100000000 (1,000,000₮) | 24.00 | 6 | MONTHS | 2026-03-02 | Asia/Hovd | DAYS_30 | DAYS_360 | Same as ls-001, alternate tz (Hovd, +07, no DST) — pins tz-to-civil-date boundary |
| ls-003-zero-interest-evendiv | 120000000 (1,200,000₮) | 0.00 | 6 | MONTHS | 2026-03-02 | Asia/Ulaanbaatar | DAYS_30 | DAYS_360 | 0% rate, principal divides evenly by 6 — sanity check equal split |
| ls-004-zero-interest-unevendiv | 100000100 (1,000,001.00₮) | 0.00 | 7 | MONTHS | 2026-04-15 | Asia/Hovd | DAYS_30 | DAYS_360 | 0% rate, principal does NOT divide evenly — exercises §6 residual absorption at zero rate |
| ls-005-uneven-principal | 100000099 | 18.50 | 9 | MONTHS | 2026-01-15 | Asia/Ulaanbaatar | DAYS_30 | DAYS_360 | Odd (non-round) principal, non-zero rate — §6 residual absorption, general case |
| ls-006-uneven-principal-long | 733333337 (7,333,333.37₮) | 21.75 | 24 | MONTHS | 2026-02-10 | Asia/Hovd | DAYS_30 | DAYS_360 | Long term (24mo), fractional-basis-point rate, uneven principal — compounding drift over many periods |
| ls-007-single-period | 50000000 (500,000₮) | 15.00 | 1 | MONTHS | 2026-06-01 | Asia/Ulaanbaatar | DAYS_30 | DAYS_360 | Single-installment / bullet loan, §7.5 |
| ls-008-monthend-jan31 | 150000000 (1,500,000₮) | 19.99 | 6 | MONTHS | 2026-01-31 | Asia/Ulaanbaatar | DAYS_30 | DAYS_360 | Disbursement on Jan 31 — exercises month-end date-stepping clamp (Feb 28, then Mar 28 not 31), §7.4 |
| ls-009-leapyear-feb29 | 200000000 (2,000,000₮) | 12.00 | 12 | MONTHS | 2028-02-29 | Asia/Hovd | DAYS_30 | DAYS_360 | Disbursement ON Feb 29 (2028 is a leap year) — exercises leap-day date-stepping, §7.4 |
| ls-010-leapyear-crossing | 180000000 (1,800,000₮) | 16.40 | 6 | MONTHS | 2027-11-30 | Asia/Ulaanbaatar | DAYS_30 | DAYS_360 | Term (Nov 2027 → May 2028) crosses into leap-year February; also month-end (Nov 30) start |
| ls-011-weekly | 60000000 (600,000₮) | 30.00 | 12 | WEEKS | 2026-05-04 | Asia/Ulaanbaatar | DAYS_30 | DAYS_360 | WEEKS frequency — exercises `rateFactorByRepaymentEveryWeek` (7-day multiplier) path distinct from monthly |
| ls-012-daily | 20000000 (200,000₮) | 36.00 | 30 | DAYS | 2026-07-01 | Asia/Hovd | DAYS_30 | DAYS_360 | DAYS frequency — exercises `rateFactorByRepaymentEveryDay` path |
| ls-013-actual-actual | 100000000 (1,000,000₮) | 24.00 | 6 | MONTHS | 2026-03-02 | Asia/Ulaanbaatar | ACTUAL | ACTUAL | Alternate day-count convention (§4.3) — same principal/rate/term as ls-001 for direct A/B comparison against fixed-30/360 |
| ls-014-actual-actual-leapyear | 100000000 (1,000,000₮) | 24.00 | 12 | MONTHS | 2027-09-01 | Asia/Ulaanbaatar | ACTUAL | ACTUAL | ACTUAL/ACTUAL term spanning the 2028 leap-year boundary — exercises `calculatePeriodFractions` cross-year split, §4.3 |
| ls-015-high-precision-rate | 250000000 (2,500,000₮) | 13.75 | 18 | MONTHS | 2026-09-10 | Asia/Hovd | DAYS_30 | DAYS_360 | Non-round rate (13.75%) to stress intermediate-precision rounding at each `mc` step |
| ls-016-small-principal-long-term | 500000 (5,000₮) | 24.00 | 24 | MONTHS | 2026-01-05 | Asia/Ulaanbaatar | DAYS_30 | DAYS_360 | Small principal over many periods — per-period EMI near the currency's 2-decimal rounding granularity, stresses §5 rounding and §6 residual absorption together |

Each row should be captured with the FULL per-period output: `periodFromDate`, `periodDueDate`, `principal`,
`interest`, `totalDue`, `outstandingLoanBalance` — not just the EMI and totals — since the reviewer re-derives
period-by-period splits, not just aggregates.

---

## 9. Go-port hazards — every `BigDecimal`/`double` site and what int64-minor-units must do instead

Independent re-derivation performed for confidence: hand-computing periods 1–3 of the shipped golden test
(principal 100.00 USD, 7.0% annual, 6 monthly periods, `DAYS_30`/`DAYS_360`, `mc=MathContext(12, HALF_UP)`) against
the formulas in §2–§4 reproduces the test's expected `EMI=17.01`, and periods 1–3 `principal=16.43/16.52/16.62`,
`interest=0.58/0.49/0.39` **exactly**, matching
`[VERIFIED: /Users/buv/fineract/fineract-progressive-loan-embeddable-schedule-generator/src/test/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGeneratorTest.java:81-83]`.
This confirms the formula chain documented above is complete enough to reproduce the oracle to the cent for the
plain case; it does not by itself validate every edge case in §7/§8, which is exactly why those need captured
vectors rather than hand-derivation.

Hazard inventory:

1. **`disbursementAmount: BigDecimal` in `LoanRepaymentScheduleModelData`** — the input principal itself is a
   `BigDecimal`, not an integer minor-unit count. The Go port's boundary adapter must convert
   `int64` minor units → the equivalent `BigDecimal`-shaped value *before* calling into any ported arithmetic, and
   the reverse on the way out; never let a `float64`/native-float intermediate exist at this boundary.
2. **`annualNominalInterestRate: BigDecimal`, percentage-shaped (`7.0` = 7%)** — `calcNominalInterestRatePercentage`
   divides by exactly `100` at the caller's `MathContext` precision
   `[VERIFIED: ProgressiveEMICalculator.java:1318-1320]`. A Go port must use an arbitrary-precision *rational* (not
   `float64`) for this division, since `interestRate/100` is frequently a non-terminating binary fraction
   (e.g. `7/100 = 0.07` terminates in decimal but the *rate factor product* over many periods will not, in
   general) — floating point here would diverge from Fineract's `BigDecimal` result after enough compounding
   periods.
3. **Every rate-factor and `fn`-recurrence step (§2.2, §4.2) is raw `BigDecimal.multiply`/`.divide(..., mc)`** —
   these are NOT `Money`-scaled (2 decimal places); they run at the full `MathContext` precision (12 or 19
   significant digits) as *dimensionless ratios*, not currency amounts. **A Go port must model this as a
   fixed-precision or arbitrary-precision decimal/rational type distinct from the int64-minor-units money type**,
   carrying the same significant-digit count and the same `RoundingMode` semantics (Go's `math/big.Rat` is exact
   but has no notion of "precision N significant digits + round"; `big.Float` has binary, not decimal, precision —
   neither is a drop-in replacement for `java.math.BigDecimal`+`MathContext`; a decimal big-rational or a
   Java-`BigDecimal`-emulating type is required to match bit-for-bit).
4. **`.divide(..., mc)` without an explicit scale relies on `MathContext`'s precision to bound the result** — if
   dividing a terminating-decimal-looking ratio (e.g. `30/360`) produces a **repeating** decimal, Java's
   `BigDecimal.divide(divisor, MathContext)` truncates/rounds to `mc.getPrecision()` significant digits using
   `mc.getRoundingMode()`. A Go implementation using plain rational arithmetic (exact, non-terminating internally)
   would NOT match unless it explicitly re-implements "round to N significant decimal digits, HALF_UP/HALF_EVEN/
   etc." at each individual `.divide()` call site, in the same order Fineract does it — not just at the very end.
   Get the *order* of rounding operations right, not only the final rounding mode.
5. **`MathUtil.stripTrailingZeros`** is applied to `rateFactorN` and `fnResult` before the final EMI division
   `[VERIFIED: ProgressiveEMICalculator.java:1725-1726]` — this changes the `BigDecimal`'s internal scale (not its
   value) but can affect the precision-counting behavior of the subsequent `.divide(..., mc)` (fewer trailing
   zeros can mean fewer digits "used up" before precision-limiting kicks in in edge cases). A Go port should
   replicate this normalization step explicitly, not assume it's a no-op.
6. **Currency-scale rounding happens exactly once per `Money.of(...)` construction, via `BigDecimal.setScale(2,
   RoundingMode)`** `[VERIFIED: Money.java:52]` — a Go port's money type should apply this rounding at the exact
   same points in the pipeline (after EMI is computed as a raw ratio-precision value, after each period's raw
   interest is computed, etc.), not batch it up or apply it earlier/later, or period-by-period drift relative to
   Fineract will accumulate and only be caught by the residual-absorption mechanism (§6) landing on a different
   value than the oracle's.
7. **`inMultiplesOf` rounding has two divergent implementations for EMI vs. down payment** (§5.3) — one uses the
   threaded `mc`, the other silently uses `MoneyHelper`'s tenant-global `MathContext`. **The Go port must pick ONE
   explicit `MathContext`-equivalent for both, sourced the same way as the oracle-capture harness configures
   `MoneyHelper`, or golden-vector rows using `installmentAmountInMultiplesOf` will not reproduce.** Recommend:
   avoid `installmentAmountInMultiplesOf` in early golden-vector rows (already done in §8) until this divergence
   is explicitly resolved as a `user`-gated decision (which `MathContext` source is canonical) rather than
   silently picking one in the port.
8. **`RoundingMode` itself is a Java enum with 7 named strategies (`UP`, `DOWN`, `CEILING`, `FLOOR`, `HALF_UP`,
   `HALF_DOWN`, `HALF_EVEN`)** — the Go port must implement the *exact same* tie-breaking semantics for whichever
   mode the oracle-capture `MathContext` uses (commonly `HALF_UP` per the shipped test, but tenant-configurable in
   production, §5.2) — an off-the-shelf Go decimal library's default rounding mode may differ (e.g.
   `shopspring/decimal` defaults vary by operation) and must be explicitly pinned, not left at a library default.
9. **`double`**: no `double`/`float` was found anywhere in the money-arithmetic call path traced in this document
   (confirmed via the reads and greps performed across `ProgressiveEMICalculator.java`, `RepaymentPeriod.java`,
   `InterestPeriod.java`, `Money.java`) — the *only* place `double` appears is in the **test assertion helper**
   `toDouble(BigDecimal)` used purely for JUnit equality comparisons, never in production arithmetic
   `[VERIFIED: EmbeddableProgressiveLoanScheduleGeneratorTest.java:120-122]`. This is worth noting explicitly: the
   golden-vector capture harness should assert on the `BigDecimal`/minor-unit string or exact integer
   representation, never round-trip through `double`, to avoid introducing a hazard that doesn't even exist in the
   Java oracle.

---

## Backlog (out of scope for this run)

- **`calculateEMIOnActualModelWithFlatInterestMethod`** (`InterestMethod.FLAT` path,
  `[VERIFIED: ProgressiveEMICalculator.java:1613-1672]`) uses a materially different formula (average of total
  disbursed+interest over period count, with remainder dumped on the last period and a reallocation pass) — not
  analyzed in depth here since the project's non-negotiables and the shipped test both use `DECLINING_BALANCE`;
  worth its own analysis pass if/when Fineract loan products using `FLAT` interest are prioritized.
- **Multi-disbursement / tranche re-amortization** (`addFullTermTrancheDisbursement`,
  `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`, `updateModelRepaymentPeriodsDuringReAge`) — real machinery
  exists in `ProgressiveEMICalculator.java` and `AdvancedPaymentScheduleTransactionProcessor.java` but is
  unreachable from the embeddable single-disbursement entry point (§7.2); relevant once the full
  `fineract-progressive-loan` bounded context (loan lifecycle, not just the PoC schedule generator) is in scope.
- **Charges, rates, tax, provisioning** — explicitly out of scope per the run brief; `LoanCharge`-related code in
  `ProgressiveLoanScheduleGenerator.java` (`applyChargesForCurrentPeriod`, `updatePeriodsWithCharges`) was noted
  but not analyzed.
- **`MoneyHelper`'s production default `RoundingMode` value and where `initializeTenantRoundingMode` is actually
  called at Fineract bootstrap** — flagged `[UNVERIFIED]` above (§5.2); needed before the Go port can assume a
  specific default without an explicit `user` decision on which mode the reference oracle capture harness pins.
- **`LoanApplicationTerms.assembleFrom(modelData, mc)`** internals beyond what was needed to trace `disbursementDatas`,
  `downPaymentAmount`, and the day-count-convention Builder plumbing — the full class is large and mostly concerns
  the full (non-embeddable) loan-account lifecycle, out of scope for the PoC schedule-generator arithmetic.
