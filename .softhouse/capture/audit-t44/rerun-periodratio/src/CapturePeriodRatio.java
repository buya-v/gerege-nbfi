/*
 * T39 -- OBSERVING the `rateFactorTillPeriodDueDate` multiplier (open P0-T34-1).
 *
 * Runs the PINNED reference oracle (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a) IN PROCESS
 * through the Path-A embeddable seam (DEC-1 section 3.2), and prints OBSERVED schedules as JSON.
 *
 * IT ASSERTS NOTHING AND PREDICTS NOTHING.  Every value printed is what the oracle emitted,
 * rendered with BigDecimal.toPlainString() -- never through a float, never rounded by this
 * harness, never scientific notation.  No expected value is synthesised here.  The predictions
 * live in ../analysis/, are produced without contacting any oracle, and are joined to this
 * output by capture id afterwards.
 *
 * WHY THIS EXISTS.  P0-T34-1 (.softhouse/reviews/T34-DEC-1-v6-rereview.md section 1) is the one
 * open P0 that is still purely RE-DERIVED.  DEC-1 section 4.3.2 and contract.go:1455-1459 write
 * the rate factor as (rate x 30 x RepaymentEvery / 360).  The pinned checkout's interest call
 * site passes `periodRatio` instead:
 *
 *   ProgressiveEMICalculator.java:1404-1413  calculateRateFactorPerPeriodForInterest
 *       BigDecimal periodRatio = switch (repaymentFrequency) { ...
 *           case MONTHS -> calculatePeriodRatio(scheduleModel, repaymentPeriod, MONTHS, mc); ... };
 *       return calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate,
 *               repaymentFrequency, periodRatio, BigDecimal.valueOf(30), daysInYear,
 *               actualDaysInPeriod, calculatedDaysInPeriod, mc);
 *
 *   ProgressiveEMICalculator.java:1536-1537  calculateRateFactorPerPeriod  (the recurrence)
 *       case DAYS_30 -> calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate,
 *               repaymentFrequency, repaymentEvery, daysInMonth, daysInYear, actualDaysInPeriod,
 *               calculatedDaysInRepaymentPeriod, mc);
 *
 * `periodRatio` equals RepaymentEvery only while every repayment period's window is
 * ScheduleStartDate + k months.  The month-end re-anchor breaks that lattice whenever the
 * re-anchor seed (the DISBURSEMENT date, LoanApplicationTerms.java:583-588 ->
 * DefaultScheduledDateGenerator.java:168-176) and calculateSeedDate's seed (the SCHEDULE START
 * date, :1461-1479) disagree.  The whole committed corpus is aligned, hence blind.
 *
 * CASE FAMILIES.
 *   T39-CAL       rig calibration at (12, HALF_UP) against a shipped USD test literal.
 *                 NEVER a parity vector.
 *   T39-CTL-*     in-graded-domain controls OUTSIDE the drift region, where every reading
 *                 agrees.  T39-CTL-Q0a additionally reproduces committed observation Q0a.
 *   T39-P0-*      INSIDE the drift region: ScheduleStartDate day in {28,29,30} with a later
 *                 same-month disbursement.  These are the cells that carry P0-T34-1.
 *   T39-ME-*      the month-end special case inside calculatePeriodRatio [:1426-1436].
 *                 T39-ME-A reproduces committed capture T37-3b-2 input for input.
 *
 * SETTINGS.  Everything except the rig calibration runs at the ratified production
 * MathContext (19, HALF_UP): MoneyHelper.PRECISION = 19 is a compile-time constant
 * [MoneyHelper.java:35, :91-93] and HALF_UP is RoundingMode ordinal 4.  Each case sets the
 * tenant rounding mode explicitly so the AMBIENT MoneyHelper context is (19, HALF_UP) too, and
 * echoes MoneyHelper.getMathContext() into its own output block.
 *
 * FULL-CELL OUTPUT.  Every per-period column the seam exposes is emitted -- periodFromDate,
 * periodDueDate, principal, interest, fee, penalty, outstanding balance, total due and total
 * outstanding balance -- plus the plan totals.  Comparing only the three headline scalars is
 * what let defect F-1 hide through five reviews (.softhouse/patterns.md).
 */
import org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant;
import org.apache.fineract.infrastructure.core.service.ThreadLocalContextUtil;
import org.apache.fineract.organisation.monetary.data.CurrencyData;
import org.apache.fineract.organisation.monetary.domain.MoneyHelper;
import org.apache.fineract.portfolio.common.domain.DaysInMonthType;
import org.apache.fineract.portfolio.common.domain.DaysInYearCustomStrategyType;
import org.apache.fineract.portfolio.common.domain.DaysInYearType;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlan;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDisbursementPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDownPaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanRepaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class CapturePeriodRatio {

    record Case(String id, String family, String purpose, LocalDate startDate,
            LocalDate disbursementDate, BigDecimal principal, int noRepayments, BigDecimal annualRate,
            int precision, RoundingMode mode, String currencyCode, int currencyDigits, DaysInMonthType dim,
            DaysInYearType diy, DaysInYearCustomStrategyType diyCustom, BigDecimal downPaymentPct,
            Integer installmentMultiplesOf, Integer fixedLength, boolean interestRecognitionOnDisbursementDate,
            boolean allowPartialPeriodInterestCalculation, boolean allowFullTermForTranche, String tenantId,
            Integer tenantRoundingMode, String tenantTimeZone) {
    }

    /**
     * A case at the ratified production settings: tenant rounding HALF_UP(4), MathContext
     * precision 19, MNT (ISO 4217 numeric 496, minor unit 2), 30/360, no down payment, no
     * installment multiple, single disbursement, monthly, declining balance.
     */
    static Case prod(String id, String family, String purpose, LocalDate start, LocalDate disb,
            String principal, int noRepayments, String rate, String tenantId) {
        return new Case(id, family, purpose, start, disb, new BigDecimal(principal), noRepayments,
                new BigDecimal(rate), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360, null, BigDecimal.ZERO, null, null, false, true, false, tenantId, 4,
                "Asia/Ulaanbaatar");
    }

    static List<Case> cases() {
        final List<Case> cases = new ArrayList<>();

        // ---- RIG CALIBRATION -------------------------------------------------------------
        // Runs at (12, HALF_UP) because that is the precision the SHIPPED test expectation was
        // produced at.  It must reproduce that literal digit for digit (level 17.01, final 17.00,
        // total interest 2.05, term 182, splits 16.43/0.58 ... 16.90/0.10) or this run is void.
        // NOT a parity vector, and never promoted as one.
        cases.add(new Case("T39-CAL", "CALIBRATION",
                "RIG CALIBRATION at (12, HALF_UP) vs the shipped USD test literal",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("100"), 6,
                new BigDecimal("7.0"), 12, RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360, null, BigDecimal.ZERO, null, null, false, true, false, "t39_cal", 4,
                "Asia/Ulaanbaatar"));

        // ---- REPRODUCTION CONTROLS --------------------------------------------------------
        // Shapes already in the committed corpus, re-taken through THIS harness.  If they do not
        // come back identical, this harness is the variable and nothing below is comparable.
        cases.add(prod("T39-CTL-Q0a", "CONTROL",
                "REPRODUCTION CONTROL vs committed observation Q0a and capture T37-CTL-Q0a",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6", "t39_ctl_q0a"));
        cases.add(prod("T39-CTL-1", "CONTROL",
                "in-graded-domain control OUTSIDE the drift region; reproduces capture T37-3-A",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1014632", 6, "7.0", "t39_ctl_1"));
        cases.add(prod("T39-CTL-2", "CONTROL",
                "in-graded-domain control OUTSIDE the drift region, mid-month start = disbursement",
                LocalDate.of(2024, 1, 15), LocalDate.of(2024, 1, 15), "1200000", 6, "21.6", "t39_ctl_2"));

        // ---- INSIDE THE DRIFT REGION -- these carry P0-T34-1 ------------------------------
        // ScheduleStartDate day in {28,29,30}; disbursement LATER in the same month with a day
        // that makes DefaultScheduledDateGenerator's re-anchor seed differ from
        // calculateSeedDate's seed, so some repayment window is not ScheduleStartDate + k months
        // and periodRatio != RepaymentEvery.
        cases.add(prod("T39-P0-A", "DRIFT",
                "T34 section 1.4's named candidate shape: start 28 Jan, disbursement 31 Jan",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6", "t39_p0_a"));
        cases.add(prod("T39-P0-B", "DRIFT",
                "T34 section 1.3's hand-worked shape: start 28 Jan, disbursement 29 Jan",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 29), "1200000", 6, "21.6", "t39_p0_b"));
        cases.add(prod("T39-P0-C", "DRIFT", "drift over 12 periods, start 29 Jan",
                LocalDate.of(2024, 1, 29), LocalDate.of(2024, 1, 31), "5000000", 12, "16.8", "t39_p0_c"));
        cases.add(prod("T39-P0-D", "DRIFT",
                "T34 section 1.4's WORST re-derived gap: 36 periods, MNT 50,000,000",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "50000000", 36, "21.6", "t39_p0_d"));
        cases.add(prod("T39-P0-E", "DRIFT", "drift in a COMMON year (2025), start 28 Jan",
                LocalDate.of(2025, 1, 28), LocalDate.of(2025, 1, 31), "1200000", 6, "21.6", "t39_p0_e"));
        cases.add(prod("T39-P0-F", "DRIFT",
                "drift on the SMALLEST principal, MNT 100 -- is there a size threshold?",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "100", 6, "21.6", "t39_p0_f"));
        cases.add(prod("T39-P0-G", "DRIFT", "drift seeded in MARCH, not January",
                LocalDate.of(2024, 3, 28), LocalDate.of(2024, 3, 31), "2500000", 6, "16.8", "t39_p0_g"));
        cases.add(prod("T39-P0-H", "DRIFT", "drift seeded in a 30-DAY month (November)",
                LocalDate.of(2024, 11, 28), LocalDate.of(2024, 11, 30), "3000000", 6, "16.8", "t39_p0_h"));

        // ---- THE MONTH-END SPECIAL CASE ----------------------------------------------------
        // calculatePeriodRatio's MONTHS arm [:1426-1436] shifts the month count by one day when
        // the repayment period's FromDate is the last day of its month and the seed day is
        // later.  Omitting those four lines makes periodRatio 2 instead of 1 on alternate
        // periods -- roughly a doubled interest charge.  These shapes trip it deliberately.
        cases.add(prod("T39-ME-A", "MONTH_END",
                "month-end special case fires on periods 2,4,6; ALSO reproduces capture T37-3b-2",
                LocalDate.of(2024, 1, 31), LocalDate.of(2024, 1, 31), "3924149", 6, "16.8", "t39_me_a"));
        cases.add(prod("T39-ME-B", "MONTH_END", "month-end special case, 31 Jan seed, 21.6 %",
                LocalDate.of(2024, 1, 31), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6", "t39_me_b"));
        cases.add(prod("T39-ME-C", "MONTH_END", "month-end special case in a COMMON year (2023)",
                LocalDate.of(2023, 1, 31), LocalDate.of(2023, 1, 31), "1200000", 6, "21.6", "t39_me_c"));
        cases.add(prod("T39-ME-D", "MONTH_END",
                "month-end special case fires on ONE period only, 30 Jan seed",
                LocalDate.of(2024, 1, 30), LocalDate.of(2024, 1, 30), "1200000", 6, "21.6", "t39_me_d"));
        return cases;
    }

    /**
     * NEGATIVE-TEST HOOKS.  Never set on a capture run; the recorded output proves it, because
     * every case echoes the precision, the mode and the tenant rounding ordinal it actually ran
     * with, and run-periodratio.sh asserts all three.  They exist so the assertion suite can be
     * shown to FAIL -- an assertion suite that has never failed has not been tested
     * (.softhouse/patterns.md).
     *
     * -Dt39.tenantRoundingModeOrdinal=N  forces every case's tenant RoundingMode ordinal to N,
     *                                    which changes MoneyHelper's AMBIENT context.
     * -Dt39.mathContextPrecision=N       forces every case's THREADED MathContext precision to N.
     * -Dt39.mathContextRoundingMode=NAME forces every case's THREADED MathContext rounding mode.
     *                                    This is the BEHAVIOURAL canary: it is the axis on which
     *                                    the emitted money actually moves.
     */
    static List<Case> applyNegativeTestOverrides(final List<Case> in) {
        final String ordinal = System.getProperty("t39.tenantRoundingModeOrdinal");
        final String precision = System.getProperty("t39.mathContextPrecision");
        final String threadedMode = System.getProperty("t39.mathContextRoundingMode");
        if (ordinal == null && precision == null && threadedMode == null) {
            return in;
        }
        final List<Case> out = new ArrayList<>();
        for (Case c : in) {
            out.add(new Case(c.id(), c.family(), c.purpose(), c.startDate(), c.disbursementDate(),
                    c.principal(), c.noRepayments(), c.annualRate(),
                    precision == null ? c.precision() : Integer.parseInt(precision),
                    threadedMode == null ? c.mode() : RoundingMode.valueOf(threadedMode),
                    c.currencyCode(), c.currencyDigits(), c.dim(), c.diy(), c.diyCustom(), c.downPaymentPct(),
                    c.installmentMultiplesOf(), c.fixedLength(), c.interestRecognitionOnDisbursementDate(),
                    c.allowPartialPeriodInterestCalculation(), c.allowFullTermForTranche(), c.tenantId(),
                    ordinal == null ? c.tenantRoundingMode() : Integer.parseInt(ordinal), c.tenantTimeZone()));
        }
        return out;
    }

    public static void main(String[] args) {
        final List<Case> cases = applyNegativeTestOverrides(cases());
        final String ordinalOverride = System.getProperty("t39.tenantRoundingModeOrdinal");
        final String precisionOverride = System.getProperty("t39.mathContextPrecision");
        final String threadedModeOverride = System.getProperty("t39.mathContextRoundingMode");

        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"task\": \"T39\",\n");
        sb.append("  \"harness\": \"CapturePeriodRatio.java\",\n");
        sb.append("  \"question\": \"P0-T34-1: is the rateFactorTillPeriodDueDate multiplier periodRatio or RepaymentEvery?\",\n");
        sb.append("  \"path\": \"A -- embeddable seam, in-process, no server, no database\",\n");
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
                .append(threadedModeOverride == null ? "null" : "\"" + threadedModeOverride + "\"").append(",\n");
        sb.append("  \"captures\": [\n");
        for (int i = 0; i < cases.size(); i++) {
            sb.append(run(cases.get(i)));
            if (i < cases.size() - 1) {
                sb.append(",");
            }
            sb.append("\n");
        }
        sb.append("  ]\n}\n");
        System.out.println(sb);
    }

    static String run(final Case c) {
        ThreadLocalContextUtil
                .setTenant(new FineractPlatformTenant(1L, c.tenantId(), c.tenantId(), c.tenantTimeZone(), null));
        MoneyHelper.initializeTenantRoundingMode(c.tenantId(), c.tenantRoundingMode());
        String ambientMathContext;
        try {
            ambientMathContext = String.valueOf(MoneyHelper.getMathContext());
        } catch (RuntimeException e) {
            ambientMathContext = e.getClass().getName() + ": " + e.getMessage();
        }

        final MathContext mc = new MathContext(c.precision(), c.mode());
        final EmbeddableProgressiveLoanScheduleGenerator generator = new EmbeddableProgressiveLoanScheduleGenerator();
        final CurrencyData currency = new CurrencyData(c.currencyCode(), c.currencyCode(), c.currencyDigits(),
                c.installmentMultiplesOf(), c.currencyCode(), c.currencyCode());

        final LoanRepaymentScheduleModelData config = new LoanRepaymentScheduleModelData(c.startDate(), currency,
                c.principal(), c.disbursementDate(), c.noRepayments(), 1, "MONTHS", c.annualRate(),
                BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0, c.dim(), c.diy(), c.downPaymentPct(),
                c.installmentMultiplesOf(), c.fixedLength(), c.interestRecognitionOnDisbursementDate(),
                c.diyCustom(), InterestMethod.DECLINING_BALANCE, c.allowPartialPeriodInterestCalculation(),
                c.allowFullTermForTranche());

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"family\": \"").append(c.family()).append("\",\n");
        b.append("      \"purpose\": \"").append(c.purpose()).append("\",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"scheduleGenerationStartDate\": \"").append(c.startDate()).append("\",\n");
        b.append("        \"disbursementDate\": \"").append(c.disbursementDate()).append("\",\n");
        b.append("        \"disbursementAmount\": \"").append(c.principal().toPlainString()).append("\",\n");
        b.append("        \"numberOfRepayments\": ").append(c.noRepayments()).append(",\n");
        b.append("        \"repaymentEvery\": 1,\n");
        b.append("        \"repaymentFrequencyType\": \"MONTHS\",\n");
        b.append("        \"annualNominalInterestRate\": \"").append(c.annualRate().toPlainString()).append("\",\n");
        b.append("        \"mathContextPrecision\": ").append(c.precision()).append(",\n");
        b.append("        \"mathContextRoundingMode\": \"").append(c.mode()).append("\",\n");
        b.append("        \"tenantId\": \"").append(c.tenantId()).append("\",\n");
        b.append("        \"tenantTimeZone\": \"").append(c.tenantTimeZone()).append("\",\n");
        b.append("        \"tenantRoundingModeOrdinal\": ").append(c.tenantRoundingMode()).append(",\n");
        b.append("        \"ambientMoneyHelperMathContext\": \"").append(ambientMathContext).append("\",\n");
        b.append("        \"currencyCode\": \"").append(c.currencyCode()).append("\",\n");
        b.append("        \"currencyDecimalPlaces\": ").append(c.currencyDigits()).append(",\n");
        b.append("        \"currencyInMultiplesOf\": ").append(c.installmentMultiplesOf()).append(",\n");
        b.append("        \"daysInMonth\": \"").append(c.dim()).append("\",\n");
        b.append("        \"daysInYear\": \"").append(c.diy()).append("\",\n");
        b.append("        \"daysInYearCustomStrategy\": ")
                .append(c.diyCustom() == null ? "null" : "\"" + c.diyCustom() + "\"").append(",\n");
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
                        + pl(dp.getPrincipalAmount()) + "\"}");
            } else if (period instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                rows.add("          {\"type\": \"DOWN_PAYMENT\", \"periodNumber\": " + dpp.periodNumber()
                        + ", \"fromDate\": \"" + dpp.periodFromDate() + "\", \"dueDate\": \"" + dpp.periodDueDate()
                        + "\", \"balance\": \"" + pl(dpp.getOutstandingLoanBalance()) + "\", \"principal\": \""
                        + pl(dpp.getPrincipalAmount()) + "\", \"total\": \"" + pl(dpp.getTotalDueAmount())
                        + "\", \"totalOutstandingBalance\": \"" + pl(dpp.getTotalOutstandingLoanBalance()) + "\"}");
            } else if (period instanceof LoanSchedulePlanRepaymentPeriod rp) {
                rows.add("          {\"type\": \"REPAYMENT\", \"periodNumber\": " + rp.periodNumber()
                        + ", \"fromDate\": \"" + rp.periodFromDate() + "\", \"dueDate\": \"" + rp.periodDueDate()
                        + "\", \"balance\": \"" + pl(rp.getOutstandingLoanBalance()) + "\", \"principal\": \""
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

    /** Plain string, never scientific notation, never a float. */
    static String pl(final BigDecimal v) {
        return v == null ? "null" : v.toPlainString();
    }
}
