/*
 * T48 -- OBSERVATION of the ACTUAL/ACTUAL cross-year PARTIAL-PERIOD arm of
 * ProgressiveEMICalculator, the one arm of the algorithm no capture in this program has
 * ever exercised.
 *
 * Runs the PINNED reference oracle (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a) IN PROCESS
 * and prints OBSERVED values as JSON.
 *
 * IT ASSERTS NOTHING AND PREDICTS NOTHING.  Every value printed is what the oracle emitted,
 * rendered with BigDecimal.toPlainString() -- never through a float, never rounded by this
 * harness, never scientific notation.  No expected value is synthesised here.
 *
 * RAW OBSERVED FORM ONLY.  Gate G-1 is open; nothing here is contract-shaped and nothing here
 * is promoted to the parity vector store.
 *
 * THIS TASK CAPTURES; IT DOES NOT ADMIT.  Nothing here proposes admitting
 * DaysInYearCustomStrategy (or ACTUAL/ACTUAL) to DEC-1's graded domain -- that would make
 * daysInYearCustomStrategy live, which DEC-1 s4.4 states is an AMENDMENT, a gate no agent
 * may cross.
 *
 * ----------------------------------------------------------------------------------------
 * TWO SEAMS, selected with -Dt48.set.  They are NOT the same seam and are labelled apart.
 *
 *   -Dt48.set=seam   PATH A -- the embeddable seam
 *                    EmbeddableProgressiveLoanScheduleGenerator.generate(mc, modelData),
 *                    exactly the seam capture passes 1/2/3, T37, T39 and T46 used.
 *                    OBSERVED LIMIT, verified from source: LoanApplicationTerms's private
 *                    Builder constructor [LoanApplicationTerms.java:304-351] never copies
 *                    builder.daysInYearCustomStrategy [declared :380, set by the builder
 *                    setter :567-570] into the field [:291], so assembleFrom's
 *                    .daysInYearCustomStrategy(...) call [:604] is DROPPED on this path.
 *                    Every seam case therefore runs with the strategy effectively UNSET,
 *                    whatever the input says.  The harness feeds the field anyway and the
 *                    payload records both what was fed and that it cannot bind.
 *
 *   -Dt48.set=calc   PATH A2 -- the EMICalculator seam, one layer below the schedule
 *                    generator: ProgressiveEMICalculator.generatePeriodInterestScheduleModel
 *                    + addDisbursement, driven with a hand-built LoanConfigurationDetails.
 *                    This is the seam Fineract's OWN shipped unit tests use
 *                    [ProgressiveEMICalculatorTest.java], and it is the only in-process seam
 *                    on which daysInYearCustomStrategy BINDS.  It also exposes
 *                    InterestPeriod.getRateFactor(), i.e. the direct output of
 *                    rateFactorByRepaymentPartialPeriod [:1969-1980].
 *                    PATH A2 IS A NEW SEAM.  Promoting a capture path to a trusted source is
 *                    a `user` decision; this pass records Path A2 observations as
 *                    observations and leans on the shipped-literal reproductions in the
 *                    CALIBRATION family to show the rig drives the oracle correctly.
 *
 *   -Dt48.set=exact  the EXACTNESS probe at :1969-1980 -- see below.
 *
 * ----------------------------------------------------------------------------------------
 * THE ARM UNDER OBSERVATION [ProgressiveEMICalculator.java]
 *
 *   :1505-1507  partialPeriodCalculationNeeded =
 *                    daysInYearType == ACTUAL
 *                 && interestPeriodDueDate.getYear() - interestPeriodFromDate.getYear() > 0
 *                 && (!FEB_29_PERIOD_ONLY.equals(daysInYearCustomStrategy)
 *                     || isPeriodContainsFeb29(repaymentPeriod.from, repaymentPeriod.due))
 *   :1526-1531  if it holds:  f = calculatePeriodFractions(...);
 *                             return rateFactorByRepaymentPartialPeriod(
 *                                        interestRate, ONE, f, ONE, ONE, mc);
 *   :1550-1568  calculatePeriodFractions accumulates, segmented at the year boundary,
 *                             SUM over years  days(segment) / Year.of(year).length()
 *               where the segment boundary is getFractionPeriodDueDateForEndOfYear
 *               [:1578-1584] = 31 December of that year, or 1 January of the next when
 *               isInterestRecognitionOnDisbursementDate() is true.
 *   :1969-1980  rateFactorByRepaymentPartialPeriod does
 *                   interestFractionPerPeriod = repaymentEvery.multiply(cumulatedPeriodRatio)
 *               with NO MathContext -- deliberately exact, unlike every neighbouring
 *               operation.  Set `exact` probes exactly that.
 *
 * SETTINGS.  Everything except the CALIBRATION family runs at the ratified production
 * threaded MathContext (19, HALF_UP).  MoneyHelper.PRECISION = 19 is a compile-time constant
 * [MoneyHelper.java:35, :91-93]; HALF_UP is RoundingMode ordinal 4.  The CALIBRATION family
 * runs at whatever settings the shipped test literal it reproduces was written at, and says
 * which.
 */
import org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant;
import org.apache.fineract.infrastructure.core.service.ThreadLocalContextUtil;
import org.apache.fineract.organisation.monetary.data.CurrencyData;
import org.apache.fineract.organisation.monetary.domain.Money;
import org.apache.fineract.organisation.monetary.domain.MoneyHelper;
import org.apache.fineract.portfolio.common.domain.DaysInMonthType;
import org.apache.fineract.portfolio.common.domain.DaysInYearCustomStrategyType;
import org.apache.fineract.portfolio.common.domain.DaysInYearType;
import org.apache.fineract.portfolio.common.domain.PeriodFrequencyType;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlan;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDisbursementPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDownPaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanRepaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.DefaultScheduledDateGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanScheduleModelRepaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanScheduleProcessingType;
import org.apache.fineract.portfolio.loanproduct.calc.ProgressiveEMICalculator;
import org.apache.fineract.portfolio.loanproduct.calc.data.InterestPeriod;
import org.apache.fineract.portfolio.loanproduct.calc.data.ProgressiveLoanInterestScheduleModel;
import org.apache.fineract.portfolio.loanproduct.calc.data.RepaymentPeriod;
import org.apache.fineract.portfolio.loanproduct.data.LoanConfigurationDetails;
import org.apache.fineract.portfolio.loanproduct.domain.AmortizationMethod;
import org.apache.fineract.portfolio.loanproduct.domain.InterestCalculationPeriodMethod;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.Year;
import java.util.ArrayList;
import java.util.List;

public class CaptureActualActual {

    // =====================================================================================
    // CASE RECORDS
    // =====================================================================================

    /** A Path A (embeddable seam) case.  Mirrors T39/T46's Case record field for field. */
    record SeamCase(String id, String family, String purpose, LocalDate startDate, LocalDate disbursementDate,
            BigDecimal principal, int noRepayments, BigDecimal annualRate, int precision, RoundingMode mode,
            String currencyCode, int currencyDigits, DaysInMonthType dim, DaysInYearType diy,
            DaysInYearCustomStrategyType diyCustom, BigDecimal downPaymentPct, Integer installmentMultiplesOf,
            Integer fixedLength, boolean interestRecognitionOnDisbursementDate,
            boolean allowPartialPeriodInterestCalculation, boolean allowFullTermForTranche, String tenantId,
            Integer tenantRoundingMode, String tenantTimeZone, String repaymentFrequencyType, int repaymentEvery) {
    }

    /**
     * A Path A2 (EMICalculator seam) case.  The repayment period boundaries are given
     * EXPLICITLY, exactly as Fineract's own shipped unit tests give them, so that a
     * CALIBRATION case can reproduce a shipped literal input for input.
     */
    record CalcCase(String id, String family, String purpose, List<LocalDate[]> periods, LocalDate disbursementDate,
            BigDecimal disbursedAmount, BigDecimal annualRate, int precision, RoundingMode mode, String currencyCode,
            int currencyDigits, int currencyInMultiplesOf, DaysInMonthType dim, DaysInYearType diy,
            DaysInYearCustomStrategyType diyCustom, PeriodFrequencyType freq, int repayEvery,
            boolean interestRecognitionOnDisbursementDate, String tenantId, Integer tenantRoundingMode,
            String tenantTimeZone, String shippedLiteralSource) {
    }

    static LocalDate[] p(int y1, int m1, int d1, int y2, int m2, int d2) {
        return new LocalDate[] { LocalDate.of(y1, m1, d1), LocalDate.of(y2, m2, d2) };
    }

    // =====================================================================================
    // SET `seam` -- PATH A, the embeddable seam
    // =====================================================================================

    /** Production settings, MNT, ACT/ACT, strategy unset.  The family under observation. */
    static SeamCase aa(String id, String purpose, LocalDate disb, String principal, int n, String rate,
            String freq, int every, String tenantId) {
        return new SeamCase(id, "AA-PARTIAL", purpose, disb, disb, new BigDecimal(principal), n,
                new BigDecimal(rate), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.ACTUAL,
                DaysInYearType.ACTUAL, null, BigDecimal.ZERO, null, null, false, true, false, tenantId, 4,
                "Asia/Ulaanbaatar", freq, every);
    }

    static List<SeamCase> seamCases() {
        final List<SeamCase> c = new ArrayList<>();

        // ---- CALIBRATION: the shipped embeddable-seam test literal ------------------------
        // EmbeddableProgressiveLoanScheduleGeneratorTest.java:43-93 -- USD 100 / 6 monthly /
        // 7.0% / DAYS_30 / DAYS_360, mc (12, HALF_UP); asserted literals at :74-77 are
        // loanTermInDays 182, totalDisbursed 100.00, totalInterest 2.05, totalRepayment 102.05.
        // Byte-for-byte T39-CAL / T46-CAL, so it is simultaneously a REPRODUCTION CONTROL of
        // a committed observation taken through a different harness.
        c.add(new SeamCase("T48-CAL", "CALIBRATION",
                "RIG CALIBRATION at (12, HALF_UP) vs the shipped USD test literal; also reproduces T39-CAL",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("100"), 6,
                new BigDecimal("7.0"), 12, RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360, null, BigDecimal.ZERO, null, null, false, true, false, "t48_cal", 4,
                "Asia/Ulaanbaatar", "MONTHS", 1));

        // ---- CONTROL: reproduce committed observations through THIS harness ---------------
        c.add(new SeamCase("T48-CTL-Q0a", "CONTROL",
                "REPRODUCTION CONTROL vs committed observations Q0a / T37-CTL-Q0a / T39-CTL-Q0a",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1200000"), 6,
                new BigDecimal("21.6"), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360, null, BigDecimal.ZERO, null, null, false, true, false, "t48_ctl_q0a", 4,
                "Asia/Ulaanbaatar", "MONTHS", 1));
        // B-03 (Path B, committed) is MNT 1,200,000 / 12 monthly / 21.6% ACT/ACT from
        // 2024-01-01 with daysInMonth ACTUAL and interestCalculationPeriodType DAILY
        // [pathb/req/product-3-diycs-fullleapyear.json, calc-B-03-diycs-fullleapyear.json];
        // reference-oracle.md records total interest 144,659.21.  Its product carries
        // daysInYearCustomStrategy FULL_LEAP_YEAR, which Path A drops -- and FULL_LEAP_YEAR is
        // a behavioural no-op anyway, so the two must agree.  Entirely inside 2024, so the
        // partial-period arm never fires: this is a CONTROL, not a capture of the arm.
        // (B-01 is NOT the right anchor for this configuration: its product sets
        // interestCalculationPeriodType 1 = SAME_AS_REPAYMENT_PERIOD
        // [pathb/req/product-1-baseline.json], which takes the early return at
        // ProgressiveEMICalculator.java:1512-1524 and never reaches the ACT/ACT branch.)
        c.add(new SeamCase("T48-CTL-B03", "CONTROL",
                "REPRODUCTION CONTROL vs committed Path B observation B-03: ACT/ACT, NO year crossing",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1200000"), 12,
                new BigDecimal("21.6"), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.ACTUAL,
                DaysInYearType.ACTUAL, null, BigDecimal.ZERO, null, null, false, true, false, "t48_ctl_b01", 4,
                "Asia/Ulaanbaatar", "MONTHS", 1));

        // ---- AA-PARTIAL: the arm itself ---------------------------------------------------
        // AA-1 / AA-2 are the SAME shape and differ ONLY in
        // isInterestRecognitionOnDisbursementDate, which is the sole input to
        // getFractionPeriodDueDateForEndOfYear [:1578-1584].  Any cell that moves between
        // them was moved by the year-boundary CHOICE (31 Dec vs 1 Jan) and by nothing else.
        c.add(aa("T48-AA-1", "leap->non-leap crossing, monthly; period 2 spans 2024-12-01..2025-01-01",
                LocalDate.of(2024, 11, 1), "1200000", 6, "21.6", "MONTHS", 1, "t48_aa_1"));
        c.add(new SeamCase("T48-AA-2", "AA-PARTIAL",
                "AA-1 with interestRecognitionOnDisbursementDate=TRUE: boundary moves 31 Dec -> 1 Jan",
                LocalDate.of(2024, 11, 1), LocalDate.of(2024, 11, 1), new BigDecimal("1200000"), 6,
                new BigDecimal("21.6"), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.ACTUAL,
                DaysInYearType.ACTUAL, null, BigDecimal.ZERO, null, null, true, true, false, "t48_aa_2", 4,
                "Asia/Ulaanbaatar", "MONTHS", 1));
        // AA-3: quarterly.  repayEvery = 3, so a port that threaded the product's repayEvery
        // into rateFactorByRepaymentPartialPeriod's `repaymentEvery` parameter instead of the
        // literal BigDecimal.ONE at the call site [:1529-1530] would treble the rate factor.
        c.add(aa("T48-AA-3", "quarterly, repayEvery=3; period 2 spans 2023-12-01..2024-03-01 (crosses AND contains Feb 29)",
                LocalDate.of(2023, 9, 1), "10000000", 4, "12.0", "MONTHS", 3, "t48_aa_3"));
        // AA-4: repayEvery = 13 months, so EVERY period crosses a year boundary and each
        // accumulates THREE segments -- the while loop [:1558-1567] runs three times.
        c.add(aa("T48-AA-4", "repayEvery=13 months, 2 periods; each period spans THREE year segments",
                LocalDate.of(2023, 12, 15), "10000000", 2, "12.0", "MONTHS", 13, "t48_aa_4"));
        c.add(aa("T48-AA-5", "non-leap -> non-leap crossing (2022->2023): both segments divide by 365",
                LocalDate.of(2022, 11, 15), "1200000", 3, "21.6", "MONTHS", 1, "t48_aa_5"));
        c.add(aa("T48-AA-6", "leap -> non-leap crossing mid-December (2024-12-15..2025-01-15): 16/366 + 15/365",
                LocalDate.of(2024, 12, 15), "1200000", 3, "21.6", "MONTHS", 1, "t48_aa_6"));
        c.add(aa("T48-AA-7", "non-leap -> leap crossing mid-December (2023-12-15..2024-01-15): 16/365 + 15/366",
                LocalDate.of(2023, 12, 15), "1200000", 3, "21.6", "MONTHS", 1, "t48_aa_7"));
        // AA-8: from-date IS 31 December, so the first segment has ZERO days.
        c.add(aa("T48-AA-8", "period starts ON 31 December: first segment is ZERO days, whole period falls in the next year",
                LocalDate.of(2024, 12, 31), "1200000", 3, "21.6", "MONTHS", 1, "t48_aa_8"));
        c.add(aa("T48-AA-9", "WEEKLY across the year boundary",
                LocalDate.of(2024, 12, 18), "1200000", 4, "21.6", "WEEKS", 1, "t48_aa_9"));
        c.add(aa("T48-AA-10", "DAILY frequency, repayEvery=10 days, across the year boundary",
                LocalDate.of(2024, 12, 22), "1200000", 3, "21.6", "DAYS", 10, "t48_aa_10"));
        // AA-11: DaysInMonthType.DAYS_30 with ACT/ACT.  The partial-period branch [:1526]
        // returns BEFORE the daysInMonthType switch [:1534-1541], so the crossing period must
        // be identical to AA-1's crossing period while the non-crossing periods must differ.
        c.add(new SeamCase("T48-AA-11", "AA-PARTIAL",
                "AA-1 with DaysInMonthType.DAYS_30: the partial arm returns BEFORE the daysInMonth switch",
                LocalDate.of(2024, 11, 1), LocalDate.of(2024, 11, 1), new BigDecimal("1200000"), 6,
                new BigDecimal("21.6"), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.DAYS_30,
                DaysInYearType.ACTUAL, null, BigDecimal.ZERO, null, null, false, true, false, "t48_aa_11", 4,
                "Asia/Ulaanbaatar", "MONTHS", 1));

        // ---- AA-NEG: the conjuncts that SUPPRESS the arm ----------------------------------
        c.add(new SeamCase("T48-AA-N1", "AA-NEG",
                "AA-1 with DaysInYearType.DAYS_365: first conjunct false, arm must NOT fire",
                LocalDate.of(2024, 11, 1), LocalDate.of(2024, 11, 1), new BigDecimal("1200000"), 6,
                new BigDecimal("21.6"), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.ACTUAL,
                DaysInYearType.DAYS_365, null, BigDecimal.ZERO, null, null, false, true, false, "t48_aa_n1", 4,
                "Asia/Ulaanbaatar", "MONTHS", 1));
        c.add(aa("T48-AA-N2", "ACT/ACT but NO year crossing: second conjunct false, arm must NOT fire",
                LocalDate.of(2024, 2, 1), "1200000", 6, "21.6", "MONTHS", 1, "t48_aa_n2"));
        // AA-N3: the input SAYS FEB_29_PERIOD_ONLY.  Path A drops it
        // [LoanApplicationTerms.java:304-351 never copies :380 into :291], so this case must
        // come back IDENTICAL to AA-1.  That identity is the OBSERVATION of the drop.
        c.add(new SeamCase("T48-AA-N3", "AA-NEG",
                "AA-1 with daysInYearCustomStrategy=FEB_29_PERIOD_ONLY FED IN: Path A drops it, so this must equal AA-1",
                LocalDate.of(2024, 11, 1), LocalDate.of(2024, 11, 1), new BigDecimal("1200000"), 6,
                new BigDecimal("21.6"), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.ACTUAL,
                DaysInYearType.ACTUAL, DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, BigDecimal.ZERO, null,
                null, false, true, false, "t48_aa_n3", 4, "Asia/Ulaanbaatar", "MONTHS", 1));
        c.add(new SeamCase("T48-AA-N4", "AA-NEG",
                "AA-1 with daysInYearCustomStrategy=FULL_LEAP_YEAR FED IN: Path A drops it, so this must equal AA-1",
                LocalDate.of(2024, 11, 1), LocalDate.of(2024, 11, 1), new BigDecimal("1200000"), 6,
                new BigDecimal("21.6"), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.ACTUAL,
                DaysInYearType.ACTUAL, DaysInYearCustomStrategyType.FULL_LEAP_YEAR, BigDecimal.ZERO, null,
                null, false, true, false, "t48_aa_n4", 4, "Asia/Ulaanbaatar", "MONTHS", 1));

        return c;
    }

    // =====================================================================================
    // SET `calc` -- PATH A2, the EMICalculator seam.  The only in-process seam on which
    // daysInYearCustomStrategy binds.
    // =====================================================================================

    /** Production settings, MNT, ACT/ACT with an explicit strategy. */
    static CalcCase prod(String id, String family, String purpose, List<LocalDate[]> periods, String amount,
            String rate, DaysInYearCustomStrategyType strat, int every, String tenantId) {
        return new CalcCase(id, family, purpose, periods, periods.get(0)[0], new BigDecimal(amount),
                new BigDecimal(rate), 19, RoundingMode.HALF_UP, "MNT", 2, 0, DaysInMonthType.ACTUAL,
                DaysInYearType.ACTUAL, strat, PeriodFrequencyType.MONTHS, every, false, tenantId, 4,
                "Asia/Ulaanbaatar", null);
    }

    /**
     * A shipped-literal reproduction.  Runs at the settings the shipped test runs at --
     * mc (12, HALF_EVEN) [ProgressiveEMICalculatorTest.java:76] with the ambient MoneyHelper
     * mode also HALF_EVEN (ordinal 6) [:97-98] -- and NOT at production settings.  Its value
     * is as a CONTROL on the rig, never as a parity vector.
     */
    static CalcCase shipped(String id, String purpose, List<LocalDate[]> periods, String amount, String rate,
            DaysInYearCustomStrategyType strat, int every, String tenantId, String src) {
        return new CalcCase(id, "CALIBRATION", purpose, periods, periods.get(0)[0], new BigDecimal(amount),
                new BigDecimal(rate), 12, RoundingMode.HALF_EVEN, "USD", 2, 1, DaysInMonthType.ACTUAL,
                DaysInYearType.ACTUAL, strat, PeriodFrequencyType.MONTHS, every, false, tenantId, 6,
                "Asia/Ulaanbaatar", src);
    }

    static List<CalcCase> calcCases() {
        final List<CalcCase> c = new ArrayList<>();

        // ---- CALIBRATION: reproduce Fineract's OWN shipped literals, input for input ------
        // All five come from ProgressiveEMICalculatorTest's nested class
        // LeapYear366OnlyForPeriodWith29thOfFebruaryTest.  Their asserted literals are
        // TRANSCRIBED into ../analysis/shipped_literals.json with file:line -- never computed.
        c.add(shipped("T48-CAL-S1", "shipped literal S1: Feb split, leap year, FEB_29_PERIOD_ONLY",
                List.of(p(2023, 12, 12, 2024, 1, 12), p(2024, 1, 12, 2024, 2, 12), p(2024, 2, 12, 2024, 3, 12),
                        p(2024, 3, 12, 2024, 4, 12), p(2024, 4, 12, 2024, 5, 12), p(2024, 5, 12, 2024, 6, 12)),
                "10000.0", "9.482", DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_cal_s1",
                "ProgressiveEMICalculatorTest.java:2983-3020 (test_leap_year_only_actual_for_loan_S1)"));
        c.add(shipped("T48-CAL-S2", "shipped literal S2: no February, leap year, FEB_29_PERIOD_ONLY",
                List.of(p(2024, 7, 23, 2024, 8, 23), p(2024, 8, 23, 2024, 9, 23), p(2024, 9, 23, 2024, 10, 23),
                        p(2024, 10, 23, 2024, 11, 23)),
                "15000.0", "12.0", DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_cal_s2",
                "ProgressiveEMICalculatorTest.java:3024-3056 (test_leap_year_only_actual_for_loan_S2)"));
        c.add(shipped("T48-CAL-S3", "shipped literal S3: February in one period, FEB_29_PERIOD_ONLY",
                List.of(p(2023, 10, 31, 2023, 11, 30), p(2023, 11, 30, 2023, 12, 31), p(2023, 12, 31, 2024, 1, 31),
                        p(2024, 1, 31, 2024, 2, 29), p(2024, 2, 29, 2024, 3, 31), p(2024, 3, 31, 2024, 4, 30)),
                "245000.0", "45.00", DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_cal_s3",
                "ProgressiveEMICalculatorTest.java:3060-3097 (test_leap_year_only_actual_for_loan_S3)"));
        c.add(shipped("T48-CAL-S4", "shipped literal S4: leap/non-leap split, no Feb month, FEB_29_PERIOD_ONLY",
                List.of(p(2024, 10, 31, 2024, 11, 30), p(2024, 11, 30, 2024, 12, 31), p(2024, 12, 31, 2025, 1, 31),
                        p(2025, 1, 31, 2025, 2, 28), p(2025, 2, 28, 2025, 3, 31), p(2025, 3, 31, 2025, 4, 30)),
                "2450", "9.99", DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_cal_s4",
                "ProgressiveEMICalculatorTest.java:3101-3137 (test_leap_year_only_actual_for_loan_S4)"));
        c.add(new CalcCase("T48-CAL-S5", "CALIBRATION",
                "shipped literal S5: no leap year at all, repayEvery=2, FEB_29_PERIOD_ONLY",
                List.of(p(2022, 10, 29, 2022, 12, 29), p(2022, 12, 29, 2023, 2, 28), p(2023, 2, 28, 2023, 4, 29),
                        p(2023, 4, 29, 2023, 6, 29), p(2023, 6, 29, 2023, 8, 29), p(2023, 8, 29, 2023, 10, 29)),
                LocalDate.of(2022, 10, 29), new BigDecimal("5000.0"), new BigDecimal("7.00"), 12,
                RoundingMode.HALF_EVEN, "USD", 2, 1, DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL,
                DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, PeriodFrequencyType.MONTHS, 2, false,
                "t48_cal_s5", 6, "Asia/Ulaanbaatar",
                "ProgressiveEMICalculatorTest.java:3141-3179 (test_leap_year_only_actual_for_loan_S5)"));

        // ---- FEB29: the two effects of FEB_29_PERIOD_ONLY, at PRODUCTION settings ---------
        // The shipped quarterly shape, at production settings and in MNT.  Three strategies
        // over one identical set of period boundaries.  Period 2 (index 1) spans
        // 2023-12-01..2024-03-01: it CROSSES the year boundary AND contains 29 Feb 2024, so
        // the third conjunct of partialPeriodCalculationNeeded [:1507] holds under
        // FEB_29_PERIOD_ONLY and the partial-period arm fires for ALL THREE strategies.
        // Period 3 (index 2) spans 2024-03-01..2024-06-01: no crossing, no Feb 29, so only
        // effect (a) -- the 366 -> 365 substitution -- can move it.
        final List<LocalDate[]> q = List.of(p(2023, 9, 1, 2023, 12, 1), p(2023, 12, 1, 2024, 3, 1),
                p(2024, 3, 1, 2024, 6, 1), p(2024, 6, 1, 2024, 9, 1));
        c.add(prod("T48-F29-Q-NULL", "FEB29", "quarterly cross-year, strategy UNSET", q, "10000000", "12.0",
                null, 3, "t48_f29_q_null"));
        c.add(prod("T48-F29-Q-FULL", "FEB29", "quarterly cross-year, FULL_LEAP_YEAR", q, "10000000", "12.0",
                DaysInYearCustomStrategyType.FULL_LEAP_YEAR, 3, "t48_f29_q_full"));
        c.add(prod("T48-F29-Q-F29", "FEB29", "quarterly cross-year, FEB_29_PERIOD_ONLY", q, "10000000", "12.0",
                DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 3, "t48_f29_q_f29"));

        // The SECOND effect, isolated.  Monthly periods spanning 2024-11-01..2025-05-01.
        // Period 2 (index 1) spans 2024-12-01..2025-01-01: it CROSSES the year boundary and
        // contains NO 29 February.  Under FEB_29_PERIOD_ONLY the third conjunct of
        // partialPeriodCalculationNeeded is FALSE, so the cross-year partial arm is
        // SUPPRESSED and the period falls through to the daysInMonth switch instead.
        // Under UNSET / FULL_LEAP_YEAR the arm FIRES.  No other period differs.
        final List<LocalDate[]> m = List.of(p(2024, 11, 1, 2024, 12, 1), p(2024, 12, 1, 2025, 1, 1),
                p(2025, 1, 1, 2025, 2, 1), p(2025, 2, 1, 2025, 3, 1), p(2025, 3, 1, 2025, 4, 1),
                p(2025, 4, 1, 2025, 5, 1));
        c.add(prod("T48-F29-M-NULL", "FEB29-EFFECT-B", "monthly cross-year with NO Feb 29, strategy UNSET", m,
                "1200000", "21.6", null, 1, "t48_f29_m_null"));
        c.add(prod("T48-F29-M-FULL", "FEB29-EFFECT-B", "monthly cross-year with NO Feb 29, FULL_LEAP_YEAR", m,
                "1200000", "21.6", DaysInYearCustomStrategyType.FULL_LEAP_YEAR, 1, "t48_f29_m_full"));
        c.add(prod("T48-F29-M-F29", "FEB29-EFFECT-B", "monthly cross-year with NO Feb 29, FEB_29_PERIOD_ONLY",
                m, "1200000", "21.6", DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_f29_m_f29"));

        // The companion: a one-year monthly schedule WITH a 29 February period and a
        // cross-year period that also contains no Feb 29.  2023-12-01..2024-12-01.
        // Period 1 (index 0) 2023-12-01..2024-01-01 crosses, no Feb 29 -> effect (b).
        // Period 3 (index 2) 2024-02-01..2024-03-01 contains Feb 29 -> effect (a) keeps 366.
        // Period 4..12 are in leap year 2024 without Feb 29 -> effect (a) drops 366 to 365.
        final List<LocalDate[]> y = new ArrayList<>();
        for (int i = 0; i < 12; i++) {
            LocalDate f = LocalDate.of(2023, 12, 1).plusMonths(i);
            y.add(new LocalDate[] { f, f.plusMonths(1) });
        }
        c.add(prod("T48-F29-Y-NULL", "FEB29", "12 monthly 2023-12-01.., strategy UNSET", y, "1200000", "21.6",
                null, 1, "t48_f29_y_null"));
        c.add(prod("T48-F29-Y-FULL", "FEB29", "12 monthly 2023-12-01.., FULL_LEAP_YEAR", y, "1200000", "21.6",
                DaysInYearCustomStrategyType.FULL_LEAP_YEAR, 1, "t48_f29_y_full"));
        c.add(prod("T48-F29-Y-F29", "FEB29", "12 monthly 2023-12-01.., FEB_29_PERIOD_ONLY", y, "1200000",
                "21.6", DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_f29_y_f29"));

        // EFFECT (b) IN PURE ISOLATION.  Two monthly periods, 2023-11-01..2024-01-01.
        // Effect (a) -- the 366 -> 365 substitution -- can only fire where
        // DaysInYearType.ACTUAL.getNumberOfDays(interestPeriodFromDate) is 366
        // [DaysInYearType.java:81-86 -> referenceDate.lengthOfYear()], i.e. where the
        // FROM-DATE's year is a leap year.  Both periods here start in 2023, which is NOT a
        // leap year, so effect (a) is a provable no-op on every period.  Period 2 (index 1)
        // spans 2023-12-01..2024-01-01: it crosses the boundary and contains no 29 February,
        // so the ONLY thing FEB_29_PERIOD_ONLY can change here is the third conjunct of
        // partialPeriodCalculationNeeded [:1507] -- effect (b).  Every differing cell between
        // -NULL and -F29 is therefore attributable to effect (b) and to nothing else.
        final List<LocalDate[]> pureB = List.of(p(2023, 11, 1, 2023, 12, 1), p(2023, 12, 1, 2024, 1, 1));
        c.add(prod("T48-F29-B-NULL", "FEB29-EFFECT-B-PURE",
                "effect (b) ISOLATED: both periods start in non-leap 2023, strategy UNSET", pureB,
                "1200000", "21.6", null, 1, "t48_f29_b_null"));
        c.add(prod("T48-F29-B-FULL", "FEB29-EFFECT-B-PURE",
                "effect (b) ISOLATED, FULL_LEAP_YEAR", pureB, "1200000", "21.6",
                DaysInYearCustomStrategyType.FULL_LEAP_YEAR, 1, "t48_f29_b_full"));
        c.add(prod("T48-F29-B-F29", "FEB29-EFFECT-B-PURE",
                "effect (b) ISOLATED, FEB_29_PERIOD_ONLY", pureB, "1200000", "21.6",
                DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_f29_b_f29"));

        // EFFECT (a) IN PURE ISOLATION.  Three monthly periods inside leap year 2024, none
        // containing 29 February and none crossing a year boundary, so effect (b) cannot
        // fire at all and the partial-period arm is never reached.
        final List<LocalDate[]> pureA = List.of(p(2024, 3, 1, 2024, 4, 1), p(2024, 4, 1, 2024, 5, 1),
                p(2024, 5, 1, 2024, 6, 1));
        c.add(prod("T48-F29-A-NULL", "FEB29-EFFECT-A-PURE",
                "effect (a) ISOLATED: inside leap 2024, no Feb 29, no crossing, strategy UNSET", pureA,
                "1200000", "21.6", null, 1, "t48_f29_a_null"));
        c.add(prod("T48-F29-A-FULL", "FEB29-EFFECT-A-PURE", "effect (a) ISOLATED, FULL_LEAP_YEAR", pureA,
                "1200000", "21.6", DaysInYearCustomStrategyType.FULL_LEAP_YEAR, 1, "t48_f29_a_full"));
        c.add(prod("T48-F29-A-F29", "FEB29-EFFECT-A-PURE", "effect (a) ISOLATED, FEB_29_PERIOD_ONLY", pureA,
                "1200000", "21.6", DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_f29_a_f29"));

        // The control for effect (a): the SAME leap-year window, but the middle period
        // CONTAINS 29 February, so FEB_29_PERIOD_ONLY must leave that period at 366 and
        // agree with FULL_LEAP_YEAR on its rate factor.
        final List<LocalDate[]> hasFeb = List.of(p(2024, 1, 15, 2024, 2, 15), p(2024, 2, 15, 2024, 3, 15),
                p(2024, 3, 15, 2024, 4, 15));
        c.add(prod("T48-F29-C-NULL", "FEB29-EFFECT-A-PURE",
                "middle period CONTAINS 29 Feb 2024; strategy UNSET", hasFeb, "1200000", "21.6", null, 1,
                "t48_f29_c_null"));
        c.add(prod("T48-F29-C-F29", "FEB29-EFFECT-A-PURE",
                "middle period CONTAINS 29 Feb 2024; FEB_29_PERIOD_ONLY keeps 366 there", hasFeb, "1200000",
                "21.6", DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_f29_c_f29"));

        // ---- CONTROL: reproduce the committed Path B observations B-03 and B-04 ----------
        // Same shape as .softhouse/capture/pathb/req/calc-B-03/B-04: MNT 1,200,000, 12 monthly
        // periods from 2024-01-01, 21.6%, ACT/ACT, daysInMonth ACTUAL, interest calculation
        // period DAILY.  reference-oracle.md records B-03 (FULL_LEAP_YEAR) total interest
        // 144,659.21 and B-04 (FEB_29_PERIOD_ONLY) 145,011.43, 12/12 periods differing.
        // Reproducing both through a DIFFERENT seam anchors this pass to observations the
        // program already holds.
        final List<LocalDate[]> b03 = new ArrayList<>();
        for (int i = 0; i < 12; i++) {
            LocalDate f = LocalDate.of(2024, 1, 1).plusMonths(i);
            b03.add(new LocalDate[] { f, f.plusMonths(1) });
        }
        c.add(prod("T48-A2-CTL-B03", "CONTROL",
                "REPRODUCTION CONTROL vs committed Path B observation B-03 (FULL_LEAP_YEAR)", b03, "1200000",
                "21.6", DaysInYearCustomStrategyType.FULL_LEAP_YEAR, 1, "t48_a2_ctl_b03"));
        c.add(prod("T48-A2-CTL-B04", "CONTROL",
                "REPRODUCTION CONTROL vs committed Path B observation B-04 (FEB_29_PERIOD_ONLY)", b03,
                "1200000", "21.6", DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY, 1, "t48_a2_ctl_b04"));
        c.add(prod("T48-A2-CTL-B03NULL", "CONTROL",
                "the same shape with the strategy UNSET -- must equal B-03 if FULL_LEAP_YEAR is a no-op",
                b03, "1200000", "21.6", null, 1, "t48_a2_ctl_b03null"));

        // ---- AA-PARTIAL through Path A2, so the RATE FACTOR itself is observable ----------
        final List<LocalDate[]> aa1 = List.of(p(2024, 11, 1, 2024, 12, 1), p(2024, 12, 1, 2025, 1, 1),
                p(2025, 1, 1, 2025, 2, 1), p(2025, 2, 1, 2025, 3, 1), p(2025, 3, 1, 2025, 4, 1),
                p(2025, 4, 1, 2025, 5, 1));
        c.add(prod("T48-A2-AA1", "AA-PARTIAL", "Path A2 twin of seam case T48-AA-1; exposes the rate factor",
                aa1, "1200000", "21.6", null, 1, "t48_a2_aa1"));
        c.add(new CalcCase("T48-A2-AA2", "AA-PARTIAL",
                "Path A2 twin of T48-AA-2: interestRecognitionOnDisbursementDate=TRUE moves the boundary to 1 Jan",
                aa1, LocalDate.of(2024, 11, 1), new BigDecimal("1200000"), new BigDecimal("21.6"), 19,
                RoundingMode.HALF_UP, "MNT", 2, 0, DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL, null,
                PeriodFrequencyType.MONTHS, 1, true, "t48_a2_aa2", 4, "Asia/Ulaanbaatar", null));

        return c;
    }

    // =====================================================================================
    // MAIN
    // =====================================================================================

    public static void main(String[] args) {
        final String set = System.getProperty("t48.set", "seam");
        final String ordinalOverride = System.getProperty("t48.tenantRoundingModeOrdinal");
        final String precisionOverride = System.getProperty("t48.mathContextPrecision");
        final String modeOverride = System.getProperty("t48.mathContextRoundingMode");

        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"task\": \"T48\",\n");
        sb.append("  \"harness\": \"CaptureActualActual.java\",\n");
        sb.append("  \"set\": \"").append(set).append("\",\n");
        sb.append("  \"question\": \"").append(switch (set) {
            case "seam" -> "DEC-1 s8: the ACTUAL/ACTUAL cross-year partial-period arm, through the Path A embeddable seam";
            case "calc" -> "the same arm plus FEB_29_PERIOD_ONLY's two effects, through the Path A2 EMICalculator seam";
            case "exact" -> "is the NO-MathContext multiply at ProgressiveEMICalculator.java:1975 observable at the sole call site";
            default -> throw new IllegalArgumentException("unknown -Dt48.set=" + set);
        }).append("\",\n");
        sb.append("  \"path\": \"").append(switch (set) {
            case "seam" -> "A -- embeddable seam, in-process, no server, no database";
            case "calc", "exact" -> "A2 -- ProgressiveEMICalculator seam, in-process, no server, no database";
            default -> "?";
        }).append("\",\n");
        sb.append("  \"capturesNotAdmits\": \"This pass records RAW OBSERVATIONS ONLY. It does NOT propose admitting "
                + "DaysInYearCustomStrategy or ACTUAL/ACTUAL to DEC-1's graded domain; that is an amendment (DEC-1 s4.4) "
                + "and a gate no agent may cross. Gate G-1 is open, so nothing here is contract-shaped or promoted.\",\n");
        sb.append("  \"fineractCommit\": \"426a23544e8426a38ae43ae404670a0a7e85b9eb\",\n");
        sb.append("  \"moneyHelperPrecisionConstant\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append("  \"javaVersion\": \"").append(System.getProperty("java.version")).append("\",\n");
        sb.append("  \"javaVmName\": \"").append(System.getProperty("java.vm.name")).append("\",\n");
        sb.append("  \"javaVmVersion\": \"").append(System.getProperty("java.vm.version")).append("\",\n");
        sb.append("  \"javaVendor\": \"").append(System.getProperty("java.vendor")).append("\",\n");
        sb.append("  \"jvmUserTimezone\": \"").append(System.getProperty("user.timezone")).append("\",\n");
        sb.append("  \"jvmFileEncoding\": \"").append(System.getProperty("file.encoding")).append("\",\n");
        sb.append("  \"negativeTestTenantRoundingModeOrdinalOverride\": ")
                .append(ordinalOverride == null ? "null" : "\"" + ordinalOverride + "\"").append(",\n");
        sb.append("  \"negativeTestMathContextPrecisionOverride\": ")
                .append(precisionOverride == null ? "null" : "\"" + precisionOverride + "\"").append(",\n");
        sb.append("  \"negativeTestMathContextRoundingModeOverride\": ")
                .append(modeOverride == null ? "null" : "\"" + modeOverride + "\"").append(",\n");
        sb.append("  \"captures\": [\n");

        final List<String> blocks = new ArrayList<>();
        switch (set) {
            case "seam" -> {
                for (SeamCase c : applySeamOverrides(seamCases())) {
                    blocks.add(runSeam(c));
                }
            }
            case "calc" -> {
                for (CalcCase c : applyCalcOverrides(calcCases())) {
                    blocks.add(runCalc(c));
                }
            }
            case "exact" -> {
                for (CalcCase c : applyCalcOverrides(calcCases())) {
                    blocks.add(runExact(c));
                }
                blocks.add(vacuityCanary());
            }
            default -> throw new IllegalArgumentException("unknown set");
        }
        sb.append(String.join(",\n", blocks)).append("\n");
        sb.append("  ]\n}\n");
        System.out.println(sb);
    }

    // --- negative-test overrides.  Present so the recipe can be PROVED FAILABLE. ----------

    static List<SeamCase> applySeamOverrides(List<SeamCase> in) {
        final String ord = System.getProperty("t48.tenantRoundingModeOrdinal");
        final String prec = System.getProperty("t48.mathContextPrecision");
        final String mode = System.getProperty("t48.mathContextRoundingMode");
        if (ord == null && prec == null && mode == null) {
            return in;
        }
        final List<SeamCase> out = new ArrayList<>();
        for (SeamCase c : in) {
            out.add(new SeamCase(c.id(), c.family(), c.purpose(), c.startDate(), c.disbursementDate(),
                    c.principal(), c.noRepayments(), c.annualRate(),
                    prec == null ? c.precision() : Integer.parseInt(prec),
                    mode == null ? c.mode() : RoundingMode.valueOf(mode), c.currencyCode(), c.currencyDigits(),
                    c.dim(), c.diy(), c.diyCustom(), c.downPaymentPct(), c.installmentMultiplesOf(),
                    c.fixedLength(), c.interestRecognitionOnDisbursementDate(),
                    c.allowPartialPeriodInterestCalculation(), c.allowFullTermForTranche(), c.tenantId(),
                    ord == null ? c.tenantRoundingMode() : Integer.parseInt(ord), c.tenantTimeZone(),
                    c.repaymentFrequencyType(), c.repaymentEvery()));
        }
        return out;
    }

    static List<CalcCase> applyCalcOverrides(List<CalcCase> in) {
        final String ord = System.getProperty("t48.tenantRoundingModeOrdinal");
        final String prec = System.getProperty("t48.mathContextPrecision");
        final String mode = System.getProperty("t48.mathContextRoundingMode");
        if (ord == null && prec == null && mode == null) {
            return in;
        }
        final List<CalcCase> out = new ArrayList<>();
        for (CalcCase c : in) {
            out.add(new CalcCase(c.id(), c.family(), c.purpose(), c.periods(), c.disbursementDate(),
                    c.disbursedAmount(), c.annualRate(),
                    prec == null ? c.precision() : Integer.parseInt(prec),
                    mode == null ? c.mode() : RoundingMode.valueOf(mode), c.currencyCode(), c.currencyDigits(),
                    c.currencyInMultiplesOf(), c.dim(), c.diy(), c.diyCustom(), c.freq(), c.repayEvery(),
                    c.interestRecognitionOnDisbursementDate(), c.tenantId(),
                    ord == null ? c.tenantRoundingMode() : Integer.parseInt(ord), c.tenantTimeZone(),
                    c.shippedLiteralSource()));
        }
        return out;
    }

    // =====================================================================================
    // PATH A -- the embeddable seam
    // =====================================================================================

    static String runSeam(final SeamCase c) {
        final String ambient = setTenantAndReadAmbient(c.tenantId(), c.tenantTimeZone(), c.tenantRoundingMode());

        // THREADED context: the object handed to generate().  Everything below is read OFF
        // THIS REFERENCE, never off the case record (T42 rule 2; T44 finding F39-3).
        final MathContext mc = new MathContext(c.precision(), c.mode());
        final EmbeddableProgressiveLoanScheduleGenerator generator = new EmbeddableProgressiveLoanScheduleGenerator();
        final CurrencyData currency = new CurrencyData(c.currencyCode(), c.currencyCode(), c.currencyDigits(),
                c.installmentMultiplesOf(), c.currencyCode(), c.currencyCode());

        final LoanRepaymentScheduleModelData config = new LoanRepaymentScheduleModelData(c.startDate(), currency,
                c.principal(), c.disbursementDate(), c.noRepayments(), c.repaymentEvery(),
                c.repaymentFrequencyType(), c.annualRate(),
                BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0, c.dim(), c.diy(), c.downPaymentPct(),
                c.installmentMultiplesOf(), c.fixedLength(), c.interestRecognitionOnDisbursementDate(),
                c.diyCustom(), InterestMethod.DECLINING_BALANCE, c.allowPartialPeriodInterestCalculation(),
                c.allowFullTermForTranche());

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"seam\": \"PATH_A\",\n");
        b.append("      \"family\": \"").append(c.family()).append("\",\n");
        b.append("      \"purpose\": \"").append(c.purpose()).append("\",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"scheduleGenerationStartDate\": \"").append(c.startDate()).append("\",\n");
        b.append("        \"disbursementDate\": \"").append(c.disbursementDate()).append("\",\n");
        b.append("        \"disbursementAmount\": \"").append(c.principal().toPlainString()).append("\",\n");
        b.append("        \"numberOfRepayments\": ").append(c.noRepayments()).append(",\n");
        b.append("        \"repaymentEvery\": ").append(c.repaymentEvery()).append(",\n");
        b.append("        \"repaymentFrequencyType\": \"").append(c.repaymentFrequencyType()).append("\",\n");
        b.append("        \"annualNominalInterestRate\": \"").append(c.annualRate().toPlainString()).append("\",\n");
        b.append("        \"mathContextPrecision\": ").append(c.precision()).append(",\n");
        b.append("        \"mathContextRoundingMode\": \"").append(c.mode()).append("\",\n");
        b.append(threadedEcho(mc, "PATH_A -- this MathContext object is the argument of "
                + "EmbeddableProgressiveLoanScheduleGenerator.generate(mc, modelData) [seam class :44-46], which "
                + "forwards the SAME object to ProgressiveLoanScheduleGenerator.generate(mc, modelData), which "
                + "reaches ProgressiveEMICalculator via generatePeriodInterestScheduleModel(..., mc) "
                + "[ProgressiveLoanScheduleGenerator.java:108-109]"));
        b.append(tenantEcho(c.tenantId(), c.tenantTimeZone(), c.tenantRoundingMode(), ambient));
        b.append("        \"currencyCode\": \"").append(c.currencyCode()).append("\",\n");
        b.append("        \"currencyDecimalPlaces\": ").append(c.currencyDigits()).append(",\n");
        b.append("        \"currencyInMultiplesOf\": ").append(c.installmentMultiplesOf()).append(",\n");
        b.append("        \"daysInMonth\": \"").append(c.dim()).append("\",\n");
        b.append("        \"daysInYear\": \"").append(c.diy()).append("\",\n");
        b.append("        \"daysInYearCustomStrategyFedIn\": ")
                .append(c.diyCustom() == null ? "null" : "\"" + c.diyCustom() + "\"").append(",\n");
        b.append("        \"daysInYearCustomStrategyCanBind\": false,\n");
        b.append("        \"daysInYearCustomStrategyBindNote\": \"On PATH A this input is accepted and silently "
                + "dropped: LoanApplicationTerms's private Builder constructor [LoanApplicationTerms.java:304-351] "
                + "never copies builder.daysInYearCustomStrategy [:380] into the field [:291], so "
                + "toLoanConfigurationDetails() [:1746-1756] passes null regardless of what assembleFrom set "
                + "[:604].\",\n");
        b.append("        \"downPaymentEnabled\": ")
                .append(BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0).append(",\n");
        b.append("        \"downPaymentPercentage\": \"").append(c.downPaymentPct().toPlainString()).append("\",\n");
        b.append("        \"installmentAmountInMultiplesOf\": ").append(c.installmentMultiplesOf()).append(",\n");
        b.append("        \"fixedLength\": ").append(c.fixedLength()).append(",\n");
        b.append("        \"interestRecognitionOnDisbursementDate\": ")
                .append(c.interestRecognitionOnDisbursementDate()).append(",\n");
        b.append("        \"interestMethod\": \"DECLINING_BALANCE\",\n");
        b.append("        \"allowPartialPeriodInterestCalculation\": ")
                .append(c.allowPartialPeriodInterestCalculation()).append(",\n");
        b.append("        \"allowFullTermForTranche\": ").append(c.allowFullTermForTranche()).append("\n");
        b.append("      },\n");

        final LoanSchedulePlan plan;
        try {
            plan = generator.generate(mc, config);
        } catch (RuntimeException e) {
            b.append("      \"observed\": null,\n");
            b.append("      \"error\": \"").append(e.getClass().getName()).append(": ")
                    .append(String.valueOf(e.getMessage()).replace("\"", "'").replace("\n", " ")).append("\"\n");
            b.append("    }");
            return b.toString();
        }

        b.append("      \"observed\": {\n");
        b.append("        \"loanTermInDays\": ").append(plan.getLoanTermInDays()).append(",\n");
        b.append("        \"totalDisbursedAmount\": \"").append(pl(plan.getTotalDisbursedAmount())).append("\",\n");
        b.append("        \"totalInterestAmount\": \"").append(pl(plan.getTotalInterestAmount())).append("\",\n");
        b.append("        \"totalRepaymentAmount\": \"").append(pl(plan.getTotalRepaymentAmount())).append("\",\n");
        b.append("        \"periods\": [\n");

        final List<String> rows = new ArrayList<>();
        for (LoanSchedulePlanPeriod period : plan.getPeriods()) {
            if (period instanceof LoanSchedulePlanDisbursementPeriod dp) {
                rows.add("          {\"type\": \"DISBURSEMENT\", \"fromDate\": \"" + dp.periodFromDate()
                        + "\", \"dueDate\": \"" + dp.periodDueDate() + "\", \"principal\": \""
                        + pl(dp.getPrincipalAmount()) + "\", \"balance\": \""
                        + pl(dp.getOutstandingLoanBalance()) + "\"}");
            } else if (period instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                rows.add("          {\"type\": \"DOWN_PAYMENT\", \"periodNumber\": " + dpp.periodNumber()
                        + ", \"fromDate\": \"" + dpp.periodFromDate() + "\", \"dueDate\": \"" + dpp.periodDueDate()
                        + "\", \"balance\": \"" + pl(dpp.getOutstandingLoanBalance()) + "\", \"principal\": \""
                        + pl(dpp.getPrincipalAmount()) + "\", \"total\": \"" + pl(dpp.getTotalDueAmount())
                        + "\", \"totalOutstandingBalance\": \"" + pl(dpp.getTotalOutstandingLoanBalance()) + "\"}");
            } else if (period instanceof LoanSchedulePlanRepaymentPeriod rp) {
                final long days = rp.periodFromDate() == null || rp.periodDueDate() == null ? -1
                        : java.time.temporal.ChronoUnit.DAYS.between(rp.periodFromDate(), rp.periodDueDate());
                final boolean crosses = rp.periodFromDate() != null && rp.periodDueDate() != null
                        && rp.periodDueDate().getYear() > rp.periodFromDate().getYear();
                rows.add("          {\"type\": \"REPAYMENT\", \"periodNumber\": " + rp.periodNumber()
                        + ", \"fromDate\": \"" + rp.periodFromDate() + "\", \"dueDate\": \"" + rp.periodDueDate()
                        + "\", \"daysInPeriod\": " + days + ", \"crossesYearBoundary\": " + crosses
                        + ", \"balance\": \"" + pl(rp.getOutstandingLoanBalance()) + "\", \"principal\": \""
                        + pl(rp.getPrincipalAmount()) + "\", \"interest\": \"" + pl(rp.getInterestAmount())
                        + "\", \"fee\": \"" + pl(rp.getFeeAmount()) + "\", \"penalty\": \""
                        + pl(rp.getPenaltyAmount()) + "\", \"total\": \"" + pl(rp.getTotalDueAmount())
                        + "\", \"totalOutstandingBalance\": \"" + pl(rp.getTotalOutstandingLoanBalance()) + "\"}");
            } else {
                rows.add("          {\"type\": \"UNKNOWN:" + period.getClass().getName() + "\"}");
            }
        }
        b.append(String.join(",\n", rows)).append("\n");
        b.append("        ]\n");
        b.append("      }\n");
        b.append("    }");
        return b.toString();
    }

    // =====================================================================================
    // PATH A2 -- the EMICalculator seam
    // =====================================================================================

    static ProgressiveLoanInterestScheduleModel buildModel(final CalcCase c, final MathContext mc,
            final ProgressiveEMICalculator emiCalculator, final CurrencyData currency) {
        final LoanConfigurationDetails detail = new LoanConfigurationDetails(currency, c.annualRate(),
                c.annualRate(), 0, 0, 0, 0, InterestMethod.DECLINING_BALANCE,
                InterestCalculationPeriodMethod.DAILY, c.diy(), c.dim(), AmortizationMethod.EQUAL_INSTALLMENTS,
                c.freq(), c.repayEvery(), c.periods().size(), c.interestRecognitionOnDisbursementDate(),
                c.diyCustom(), true, false, null, null, false, LoanScheduleProcessingType.HORIZONTAL);

        final List<LoanScheduleModelRepaymentPeriod> repaymentPeriods = new ArrayList<>();
        for (LocalDate[] pr : c.periods()) {
            repaymentPeriods.add(LoanScheduleModelRepaymentPeriod.repayment(0, pr[0], pr[1], null, null, null,
                    null, null, null, false, mc));
        }
        final ProgressiveLoanInterestScheduleModel model = emiCalculator
                .generatePeriodInterestScheduleModel(repaymentPeriods, detail, null, mc);
        emiCalculator.addDisbursement(model, c.disbursementDate(), Money.of(currency, c.disbursedAmount(), mc));
        return model;
    }

    static String runCalc(final CalcCase c) {
        final String ambient = setTenantAndReadAmbient(c.tenantId(), c.tenantTimeZone(), c.tenantRoundingMode());
        final MathContext mc = new MathContext(c.precision(), c.mode());
        final ProgressiveEMICalculator emiCalculator = new ProgressiveEMICalculator(
                new DefaultScheduledDateGenerator());
        final CurrencyData currency = new CurrencyData(c.currencyCode(), c.currencyCode(), c.currencyDigits(),
                c.currencyInMultiplesOf(), c.currencyCode(), c.currencyCode());

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"seam\": \"PATH_A2\",\n");
        b.append("      \"family\": \"").append(c.family()).append("\",\n");
        b.append("      \"purpose\": \"").append(c.purpose()).append("\",\n");
        b.append("      \"shippedLiteralSource\": ")
                .append(c.shippedLiteralSource() == null ? "null" : "\"" + c.shippedLiteralSource() + "\"")
                .append(",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"disbursementDate\": \"").append(c.disbursementDate()).append("\",\n");
        b.append("        \"disbursementAmount\": \"").append(c.disbursedAmount().toPlainString()).append("\",\n");
        b.append("        \"annualNominalInterestRate\": \"").append(c.annualRate().toPlainString()).append("\",\n");
        b.append("        \"repaymentFrequencyType\": \"").append(c.freq()).append("\",\n");
        b.append("        \"repayEvery\": ").append(c.repayEvery()).append(",\n");
        b.append("        \"mathContextPrecision\": ").append(c.precision()).append(",\n");
        b.append("        \"mathContextRoundingMode\": \"").append(c.mode()).append("\",\n");
        b.append(threadedEcho(mc, "PATH_A2 -- this MathContext object is the 4th argument of "
                + "ProgressiveEMICalculator.generatePeriodInterestScheduleModel(periods, detail, null, mc) and is "
                + "stored on the returned ProgressiveLoanInterestScheduleModel, which "
                + "calculateRateFactorPerPeriod reads back as scheduleModel.mc() "
                + "[ProgressiveEMICalculator.java:1487]"));
        b.append(tenantEcho(c.tenantId(), c.tenantTimeZone(), c.tenantRoundingMode(), ambient));
        b.append("        \"currencyCode\": \"").append(c.currencyCode()).append("\",\n");
        b.append("        \"currencyDecimalPlaces\": ").append(c.currencyDigits()).append(",\n");
        b.append("        \"currencyInMultiplesOf\": ").append(c.currencyInMultiplesOf()).append(",\n");
        b.append("        \"daysInMonth\": \"").append(c.dim()).append("\",\n");
        b.append("        \"daysInYear\": \"").append(c.diy()).append("\",\n");
        b.append("        \"daysInYearCustomStrategyFedIn\": ")
                .append(c.diyCustom() == null ? "null" : "\"" + c.diyCustom() + "\"").append(",\n");
        b.append("        \"daysInYearCustomStrategyCanBind\": true,\n");
        b.append("        \"interestRecognitionOnDisbursementDate\": ")
                .append(c.interestRecognitionOnDisbursementDate()).append(",\n");
        b.append("        \"interestCalculationPeriodMethod\": \"DAILY\",\n");
        b.append("        \"repaymentPeriodBoundaries\": [");
        final List<String> pb = new ArrayList<>();
        for (LocalDate[] pr : c.periods()) {
            pb.add("[\"" + pr[0] + "\", \"" + pr[1] + "\"]");
        }
        b.append(String.join(", ", pb)).append("]\n");
        b.append("      },\n");

        final ProgressiveLoanInterestScheduleModel model;
        try {
            model = buildModel(c, mc, emiCalculator, currency);
        } catch (RuntimeException e) {
            b.append("      \"observed\": null,\n");
            b.append("      \"error\": \"").append(e.getClass().getName()).append(": ")
                    .append(String.valueOf(e.getMessage()).replace("\"", "'").replace("\n", " ")).append("\"\n");
            b.append("    }");
            return b.toString();
        }

        b.append("      \"observed\": {\n");
        b.append("        \"loanTermInDays\": ").append(model.getLoanTermInDays()).append(",\n");
        b.append("        \"repaymentPeriods\": [\n");
        final List<String> rows = new ArrayList<>();
        int idx = 0;
        for (RepaymentPeriod rp : model.repaymentPeriods()) {
            final StringBuilder r = new StringBuilder();
            final boolean crosses = rp.getDueDate().getYear() > rp.getFromDate().getYear();
            r.append("          {\"index\": ").append(idx++);
            r.append(", \"fromDate\": \"").append(rp.getFromDate()).append("\"");
            r.append(", \"dueDate\": \"").append(rp.getDueDate()).append("\"");
            r.append(", \"daysInPeriod\": ")
                    .append(java.time.temporal.ChronoUnit.DAYS.between(rp.getFromDate(), rp.getDueDate()));
            r.append(", \"crossesYearBoundary\": ").append(crosses);
            r.append(", \"periodContainsFeb29\": ").append(observedContainsFeb29(rp.getFromDate(), rp.getDueDate()));
            r.append(", \"emi\": \"").append(pl(rp.getEmi().getAmount())).append("\"");
            r.append(", \"dueInterest\": \"").append(pl(rp.getDueInterest().getAmount())).append("\"");
            r.append(", \"duePrincipal\": \"").append(pl(rp.getDuePrincipal().getAmount())).append("\"");
            r.append(", \"outstandingLoanBalance\": \"").append(pl(rp.getOutstandingLoanBalance().getAmount()))
                    .append("\"");
            r.append(", \"calculatedDueInterest\": \"").append(pl(rp.getCalculatedDueInterest().getAmount()))
                    .append("\"");
            r.append(", \"rateFactorPlus1\": \"").append(pl(rp.getRateFactorPlus1())).append("\"");
            r.append(", \"interestPeriods\": [");
            final List<String> ips = new ArrayList<>();
            for (InterestPeriod ip : rp.getInterestPeriods()) {
                ips.add("{\"fromDate\": \"" + ip.getFromDate() + "\", \"dueDate\": \"" + ip.getDueDate()
                        + "\", \"rateFactor\": \"" + pl(ip.getRateFactor()) + "\", \"rateFactorTillPeriodDueDate\": \""
                        + pl(ip.getRateFactorTillPeriodDueDate()) + "\", \"calculatedDueInterest\": \""
                        + pl(ip.getCalculatedDueInterest()) + "\", \"disbursementAmount\": \""
                        + pl(ip.getDisbursementAmount().getAmount()) + "\"}");
            }
            r.append(String.join(", ", ips)).append("]}");
            rows.add(r.toString());
        }
        b.append(String.join(",\n", rows)).append("\n");
        b.append("        ]\n");
        b.append("      }\n");
        b.append("    }");
        return b.toString();
    }

    // =====================================================================================
    // SET `exact` -- the deliberately-unrounded multiply at :1975
    // =====================================================================================
    //
    // The call site [:1529-1530] passes BigDecimal.ONE as `repaymentEvery`, BigDecimal.ONE as
    // `actualDaysInPeriod` and BigDecimal.ONE as `calculatedDaysInPeriod`.  This probe reads
    // the ACTUAL cumulatedPeriodRatio the oracle computes -- by calling the oracle's OWN
    // public calculatePeriodFractions [:1550] on the model built from the case -- and then
    // reports, for that observed value:
    //
    //   exactProduct   = ONE.multiply(f)         <- what the oracle does at :1975
    //   roundedProduct = ONE.multiply(f, mc)     <- what a port that threaded mc would do
    //   plus the full downstream rate factor computed BOTH ways, and the rate factor the
    //   oracle actually produced for that interest period, read off InterestPeriod.
    //
    // The two downstream values are RE-DERIVATIONS on observed inputs and are labelled as
    // such; only `oracleRateFactor` is an oracle output.
    // =====================================================================================

    static String runExact(final CalcCase c) {
        final String ambient = setTenantAndReadAmbient(c.tenantId(), c.tenantTimeZone(), c.tenantRoundingMode());
        final MathContext mc = new MathContext(c.precision(), c.mode());
        final ProgressiveEMICalculator emiCalculator = new ProgressiveEMICalculator(
                new DefaultScheduledDateGenerator());
        final CurrencyData currency = new CurrencyData(c.currencyCode(), c.currencyCode(), c.currencyDigits(),
                c.currencyInMultiplesOf(), c.currencyCode(), c.currencyCode());

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"seam\": \"PATH_A2\",\n");
        b.append("      \"family\": \"")
                .append("CALIBRATION".equals(c.family()) ? "CALIBRATION" : "EXACTNESS-PROBE")
                .append("\",\n");
        b.append("      \"purpose\": \"observe ProgressiveEMICalculator.java:1975 repaymentEvery.multiply("
                + "cumulatedPeriodRatio) WITHOUT a MathContext, on the ACTUAL arguments of the sole call site "
                + "[:1529-1530]\",\n");
        b.append("      \"inputs\": {\n");
        b.append(threadedEcho(mc, "PATH_A2 -- handed to generatePeriodInterestScheduleModel and to "
                + "calculatePeriodFractions(model, from, due, mc) [ProgressiveEMICalculator.java:1550]"));
        b.append(tenantEcho(c.tenantId(), c.tenantTimeZone(), c.tenantRoundingMode(), ambient));
        b.append("        \"daysInYear\": \"").append(c.diy()).append("\",\n");
        b.append("        \"daysInYearCustomStrategyFedIn\": ")
                .append(c.diyCustom() == null ? "null" : "\"" + c.diyCustom() + "\"").append(",\n");
        b.append("        \"interestRecognitionOnDisbursementDate\": ")
                .append(c.interestRecognitionOnDisbursementDate()).append("\n");
        b.append("      },\n");

        final ProgressiveLoanInterestScheduleModel model;
        try {
            model = buildModel(c, mc, emiCalculator, currency);
        } catch (RuntimeException e) {
            b.append("      \"observed\": null,\n");
            b.append("      \"error\": \"").append(e.getClass().getName()).append(": ")
                    .append(String.valueOf(e.getMessage()).replace("\"", "'").replace("\n", " ")).append("\"\n");
            b.append("    }");
            return b.toString();
        }

        // calcNominalInterestRatePercentage [ProgressiveEMICalculator.java] divides the
        // annual rate by 100 under the threaded mc.  Re-derived here, and cross-checked
        // against the oracle's own rate factor below.
        final BigDecimal interestRate = c.annualRate().divide(BigDecimal.valueOf(100), mc);

        b.append("      \"observed\": {\n");
        b.append("        \"probes\": [\n");
        final List<String> rows = new ArrayList<>();
        for (RepaymentPeriod rp : model.repaymentPeriods()) {
            for (InterestPeriod ip : rp.getInterestPeriods()) {
                if (ip.getDueDate().getYear() <= ip.getFromDate().getYear()) {
                    continue; // the partial-period arm cannot fire; not a probe site
                }
                final BigDecimal f;
                try {
                    f = emiCalculator.calculatePeriodFractions(model, ip.getFromDate(), ip.getDueDate(), mc);
                } catch (RuntimeException e) {
                    rows.add("          {\"fromDate\": \"" + ip.getFromDate() + "\", \"dueDate\": \""
                            + ip.getDueDate() + "\", \"error\": \"" + e.getClass().getName() + "\"}");
                    continue;
                }
                final BigDecimal exactProduct = BigDecimal.ONE.multiply(f);
                final BigDecimal roundedProduct = BigDecimal.ONE.multiply(f, mc);
                final BigDecimal rfExact = interestRate.multiply(exactProduct, mc).multiply(BigDecimal.ONE, mc)
                        .divide(BigDecimal.ONE, mc).setScale(mc.getPrecision(), mc.getRoundingMode());
                final BigDecimal rfRounded = interestRate.multiply(roundedProduct, mc).multiply(BigDecimal.ONE, mc)
                        .divide(BigDecimal.ONE, mc).setScale(mc.getPrecision(), mc.getRoundingMode());
                final StringBuilder r = new StringBuilder();
                r.append("          {\"fromDate\": \"").append(ip.getFromDate()).append("\"");
                r.append(", \"dueDate\": \"").append(ip.getDueDate()).append("\"");
                r.append(", \"yearSegments\": ").append(segmentsJson(model, c, ip.getFromDate(), ip.getDueDate()));
                r.append(", \"cumulatedPeriodFractions\": \"").append(pl(f)).append("\"");
                r.append(", \"cumulatedPeriodFractionsPrecision\": ").append(f.precision());
                r.append(", \"cumulatedPeriodFractionsScale\": ").append(f.scale());
                r.append(", \"exactProduct_ONE_multiply_f\": \"").append(pl(exactProduct)).append("\"");
                r.append(", \"exactProductPrecision\": ").append(exactProduct.precision());
                r.append(", \"roundedProduct_ONE_multiply_f_mc\": \"").append(pl(roundedProduct)).append("\"");
                r.append(", \"roundedProductPrecision\": ").append(roundedProduct.precision());
                r.append(", \"productsBitIdentical\": ")
                        .append(exactProduct.toPlainString().equals(roundedProduct.toPlainString()));
                r.append(", \"productsNumericallyEqual\": ").append(exactProduct.compareTo(roundedProduct) == 0);
                r.append(", \"rederivedRateFactorFromExactProduct\": \"").append(pl(rfExact)).append("\"");
                r.append(", \"rederivedRateFactorFromRoundedProduct\": \"").append(pl(rfRounded)).append("\"");
                r.append(", \"rederivedRateFactorsIdentical\": ")
                        .append(rfExact.toPlainString().equals(rfRounded.toPlainString()));
                r.append(", \"oracleRateFactor\": \"").append(pl(ip.getRateFactor())).append("\"");
                r.append(", \"oracleRateFactorMatchesExactRederivation\": ")
                        .append(ip.getRateFactor() != null
                                && ip.getRateFactor().compareTo(rfExact) == 0);
                r.append("}");
                rows.add(r.toString());
            }
        }
        if (rows.isEmpty()) {
            rows.add("          {\"note\": \"no interest period on this case crosses a year boundary; the "
                    + "partial-period arm has no probe site here\"}");
        }
        b.append(String.join(",\n", rows)).append("\n");
        b.append("        ]\n");
        b.append("      }\n");
        b.append("    }");
        return b.toString();
    }

    /**
     * VACUITY CANARY for the exactness probe.
     *
     * A probe that reports "the unrounded multiply is indistinguishable from the rounded one"
     * is worthless unless the same comparison can be shown to SEPARATE on some input.  This
     * canary feeds the SAME comparison two operands that a MathContext(19) round WOULD move:
     * a 25-significant-digit ratio, and the same ratio times a non-unit multiplier.  If the
     * canary reports IDENTICAL, the probe is measuring nothing and the run is void.
     *
     * Every number here is a LOCAL CONSTRUCTION of this harness, not an oracle output, and is
     * labelled so.  Its only job is to prove the instrument moves.
     */
    static String vacuityCanary() {
        final MathContext mc = new MathContext(19, RoundingMode.HALF_UP);
        // 1/7 to 25 significant digits -- more digits than mc can hold.
        final BigDecimal wide = BigDecimal.ONE.divide(BigDecimal.valueOf(7), new MathContext(25,
                RoundingMode.HALF_UP));
        final BigDecimal exact1 = BigDecimal.ONE.multiply(wide);
        final BigDecimal rounded1 = BigDecimal.ONE.multiply(wide, mc);
        final BigDecimal three = BigDecimal.valueOf(3);
        final BigDecimal exact3 = three.multiply(wide);
        final BigDecimal rounded3 = three.multiply(wide, mc);
        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"T48-EXACT-CANARY\",\n");
        b.append("      \"seam\": \"NONE -- local BigDecimal construction, NOT an oracle output\",\n");
        b.append("      \"family\": \"EXACTNESS-CANARY\",\n");
        b.append("      \"purpose\": \"prove the exactness comparison is capable of separating at all; "
                + "a probe that can only ever say IDENTICAL measures nothing\",\n");
        b.append("      \"inputs\": {\n");
        b.append(threadedEcho(mc, "NONE -- this block contacts no Fineract code"));
        b.append("        \"note\": \"operands constructed by this harness, never observed\"\n");
        b.append("      },\n");
        b.append("      \"observed\": {\n");
        b.append("        \"probes\": [\n");
        b.append("          {\"leg\": \"multiplier=ONE, ratio wider than mc\", \"ratio\": \"").append(pl(wide))
                .append("\", \"ratioPrecision\": ").append(wide.precision())
                .append(", \"exactProduct\": \"").append(pl(exact1)).append("\", \"roundedProduct\": \"")
                .append(pl(rounded1)).append("\", \"productsBitIdentical\": ")
                .append(exact1.toPlainString().equals(rounded1.toPlainString())).append("},\n");
        b.append("          {\"leg\": \"multiplier=THREE, ratio wider than mc\", \"ratio\": \"").append(pl(wide))
                .append("\", \"ratioPrecision\": ").append(wide.precision())
                .append(", \"exactProduct\": \"").append(pl(exact3)).append("\", \"roundedProduct\": \"")
                .append(pl(rounded3)).append("\", \"productsBitIdentical\": ")
                .append(exact3.toPlainString().equals(rounded3.toPlainString())).append("}\n");
        b.append("        ]\n");
        b.append("      }\n");
        b.append("    }");
        return b.toString();
    }

    /**
     * The year segmentation calculatePeriodFractions walks [:1556-1567], re-derived from the
     * SAME source rule so that the observed fraction can be read.  RE-DERIVATION, not an
     * oracle output -- the oracle output is `cumulatedPeriodFractions` beside it.
     */
    static String segmentsJson(final ProgressiveLoanInterestScheduleModel model, final CalcCase c,
            final LocalDate from, final LocalDate due) {
        final List<String> segs = new ArrayList<>();
        int actualYear = from.getYear();
        final int endYear = due.getYear();
        LocalDate actualDate = from;
        while (actualYear <= endYear) {
            final LocalDate segDue = actualYear == endYear ? due
                    : (c.interestRecognitionOnDisbursementDate() ? LocalDate.of(actualYear + 1, 1, 1)
                            : LocalDate.of(actualYear, 12, 31));
            final long days = java.time.temporal.ChronoUnit.DAYS.between(actualDate, segDue);
            segs.add("{\"year\": " + actualYear + ", \"from\": \"" + actualDate + "\", \"to\": \"" + segDue
                    + "\", \"days\": " + days + ", \"yearLength\": " + Year.of(actualYear).length() + "}");
            actualDate = segDue;
            actualYear++;
        }
        return "[" + String.join(", ", segs) + "]";
    }

    // =====================================================================================
    // SHARED
    // =====================================================================================

    static String setTenantAndReadAmbient(String tenantId, String tz, Integer ordinal) {
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenantId, tenantId, tz, null));
        MoneyHelper.initializeTenantRoundingMode(tenantId, ordinal);
        try {
            return String.valueOf(MoneyHelper.getMathContext());
        } catch (RuntimeException e) {
            return e.getClass().getName() + ": " + e.getMessage();
        }
    }

    /** The THREADED MathContext, echoed OFF THE OBJECT (T42 rule 2; T44 finding F39-3). */
    static String threadedEcho(final MathContext mc, final String wiring) {
        return "        \"threadedMathContext\": \"" + mc.toString() + "\",\n"
                + "        \"threadedMathContextPrecision\": " + mc.getPrecision() + ",\n"
                + "        \"threadedMathContextRoundingMode\": \"" + mc.getRoundingMode() + "\",\n"
                + "        \"wiring\": \"" + wiring + "\",\n";
    }

    /**
     * The AMBIENT MoneyHelper context.  It is NOT the arithmetic on Path A or Path A2 -- both
     * construct their own MathContext and thread it.  It is recorded because it witnesses the
     * TENANT CONFIGURATION, and because the program knows of TWO ambient leaks onto the graded
     * call graph: (1) Money.<init> [Money.java:50] -> roundToMultiplesOf(BigDecimal, Integer)
     * [Money.java:154] -> MoneyHelper.getRoundingMode() [MoneyHelper.java:79], reachable only
     * at 0 decimal places WITH a positive inMultiplesOf -- MNT has 2, so no MNT case here
     * reaches it; and (2) the CHARGE rounding locus found by T46 (N46-1),
     * ProgressiveLoanScheduleGenerator.java:445-446 -> two-arg Money.of -> Money.java:114-116
     * -> Money.java:52 setScale(2, getMc().getRoundingMode()), which IS reachable at 2 decimal
     * places -- but no case in this pass carries a charge, so it is not reached here either.
     * The USD calibration cases run at inMultiplesOf = 1 with 2 decimal places, which is still
     * not 0 decimal places, so leak (1) stays shut there too.
     */
    static String tenantEcho(String tenantId, String tz, Integer ordinal, String ambient) {
        return "        \"tenantId\": \"" + tenantId + "\",\n"
                + "        \"tenantTimeZone\": \"" + tz + "\",\n"
                + "        \"tenantRoundingModeOrdinal\": " + ordinal + ",\n"
                + "        \"ambientMoneyHelperMathContext\": \"" + ambient + "\",\n"
                + "        \"ambientIsNotTheArithmeticHere\": true,\n";
    }

    /** isPeriodContainsFeb29 [ProgressiveEMICalculator.java:1330-1341], from-EXCLUSIVE to-INCLUSIVE. */
    static boolean observedContainsFeb29(final LocalDate from, final LocalDate due) {
        for (int year = from.getYear(); year <= due.getYear(); year++) {
            if (Year.isLeap(year)) {
                final LocalDate leapDay = LocalDate.of(year, 2, 29);
                if (leapDay.isAfter(from) && !leapDay.isAfter(due)) {
                    return true;
                }
            }
        }
        return false;
    }

    /** Plain string, never scientific notation, never a float. */
    static String pl(final BigDecimal v) {
        return v == null ? "null" : v.toPlainString();
    }
}
