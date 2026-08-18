/*
 * T37 -- DEC-1 section 8 BINDING CAPTURES (items 3, 3a, 3b, 3c, 3d).
 *
 * Runs the PINNED reference oracle (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a) IN PROCESS
 * through the Path-A embeddable seam (DEC-1 section 3.2), and prints OBSERVED schedules as JSON.
 *
 * IT ASSERTS NOTHING AND PREDICTS NOTHING.  Every value printed is what the oracle emitted,
 * rendered with BigDecimal.toString()/toPlainString() -- never through a float, never rounded
 * by this harness, never scientific notation.  No expected value is synthesised here.
 *
 * WHY THIS EXISTS.  DEC-1 section 8 item 3 binds: no conformance PASS may be claimed for
 * `loanschedule`, and no cutover proposed, until at least one admissible vector
 *   (3)  trips the EMI re-adjust guard                       [ProgressiveEMICalculator.java:1258-1308]
 *   (3a) separates the loop's strict ADOPTION test           [EmiAdjustment.java:46-48]
 *   (3b) separates the per-period interest ROUND-TRIP        [InterestPeriod.java:145-158]
 *   (3c) trips the guard in the LATER-DISBURSEMENT window    [n = |relatedRepaymentPeriods|]
 *   (3d) places the disbursement STRICTLY INSIDE a period    [day-count proration, DEC-1 4.1.1]
 * Every prior review produced RE-DERIVED figures for these shapes.  This program turns the
 * shapes into observations.  The shapes were chosen by ../analysis/select_shapes.py, which
 * checked (by re-derivation, not by oracle) that each one actually separates the readings.
 *
 * SETTINGS.  Everything except the rig calibration runs at the ratified production
 * MathContext (19, HALF_UP): MoneyHelper.PRECISION = 19 is a compile-time constant
 * [MoneyHelper.java:35, :91-93] and HALF_UP is RoundingMode ordinal 4.  Each case sets the
 * tenant rounding mode explicitly so the AMBIENT MoneyHelper context is (19, HALF_UP) too, and
 * echoes MoneyHelper.getMathContext() into its own output block.  A capture at precision 12 is
 * a rig calibration and can never be a parity vector.
 *
 * EXTRA COLUMNS.  Unlike Capture3.java this harness emits periodFromDate, feeAmount and
 * penaltyAmount -- the three per-period columns audit T22 recorded as missing.
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

public class CaptureBinding {

    record Case(String id, String bindingItem, String purpose, LocalDate startDate,
            LocalDate disbursementDate, BigDecimal principal, int noRepayments, BigDecimal annualRate,
            int precision, RoundingMode mode, String currencyCode, int currencyDigits, DaysInMonthType dim,
            DaysInYearType diy, DaysInYearCustomStrategyType diyCustom, BigDecimal downPaymentPct,
            Integer installmentMultiplesOf, Integer fixedLength, boolean interestRecognitionOnDisbursementDate,
            boolean allowPartialPeriodInterestCalculation, boolean allowFullTermForTranche, String tenantId,
            Integer tenantRoundingMode, String tenantTimeZone) {
    }

    static final LocalDate D_2024_01_01 = LocalDate.of(2024, 1, 1);

    /**
     * A case at the ratified production settings: tenant rounding HALF_UP(4), MathContext
     * precision 19, MNT (ISO 4217 numeric 496, minor unit 2), 30/360, no down payment, no
     * installment multiple, single disbursement, monthly, declining balance.
     */
    static Case prod(String id, String item, String purpose, LocalDate start, LocalDate disb,
            String principal, int noRepayments, String rate, String currency, String tenantId) {
        return new Case(id, item, purpose, start, disb, new BigDecimal(principal), noRepayments,
                new BigDecimal(rate), 19, RoundingMode.HALF_UP, currency, 2, DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360, null, BigDecimal.ZERO, null, null, false, true, false, tenantId, 4,
                "Asia/Ulaanbaatar");
    }

    public static void main(String[] args) {
        final List<Case> cases = new ArrayList<>();

        // ---- RIG CALIBRATION -------------------------------------------------------------
        // Runs at (12, HALF_UP) because that is the precision the SHIPPED test expectation was
        // produced at.  It must reproduce that literal digit for digit (EMI 17.01; splits
        // 16.43/0.58 ... 16.90/0.10; term 182; total interest 2.05) or this whole run is void.
        // NOT a parity vector, and never promoted as one.
        cases.add(new Case("T37-CAL", "-", "RIG CALIBRATION at (12, HALF_UP) vs the shipped literal",
                D_2024_01_01, D_2024_01_01, BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12,
                RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, false, "t37_cal", 4, "Asia/Ulaanbaatar"));

        // ---- REPRODUCTION CONTROL --------------------------------------------------------
        // A shape already observed in the committed corpus (t23-probe-output.txt Q0a) re-taken
        // through this harness at (19, HALF_UP).  If it does not come back identical, this
        // harness differs from the one that produced the corpus and nothing below is comparable.
        cases.add(prod("T37-CTL-Q0a", "-", "REPRODUCTION CONTROL vs committed observation Q0a",
                D_2024_01_01, D_2024_01_01, "1200000", 6, "21.6", "MNT", "t37_ctl_q0a"));

        // ---- ITEM 3 -- trips the EMI re-adjust guard, and the loop CHANGES the answer ------
        // Candidates named in DEC-1 section 8 item 3 (from T23 section 6.1).
        cases.add(prod("T37-3-A", "3", "EMI re-adjust guard trips; loop-absent reading diverges",
                D_2024_01_01, D_2024_01_01, "1014632", 6, "7.0", "MNT", "t37_3_a"));
        cases.add(prod("T37-3-B", "3", "EMI re-adjust guard trips over 36 periods",
                D_2024_01_01, D_2024_01_01, "127704", 36, "16.8", "MNT", "t37_3_b"));

        // ---- ITEM 3a -- separates the loop's strict ADOPTION test -------------------------
        // The candidate named in DEC-1 section 8 item 3a (T26's sweep).  On this shape the loop
        // FIRES, builds a trial, and the adoption test REJECTS it -- so a port that omits the
        // test adopts and returns different money, while a port that never implements the loop
        // returns the same money as the oracle.  That is exactly why 3a is a separate item.
        cases.add(prod("T37-3a", "3a", "adoption test rejects the trial; no-adoption reading diverges",
                D_2024_01_01, D_2024_01_01, "100025", 12, "16.8", "MNT", "t37_3a"));

        // ---- ITEM 3b -- separates the PER-PERIOD INTEREST ROUND-TRIP ----------------------
        // The three separately MathContext-rounded operations
        //   B x rateFactorTillPeriodDueDate ; / lengthTillPeriodDueDate ; x length
        // versus the textbook `B x rateFactor`.  Candidate named in DEC-1 section 8 item 3b.
        cases.add(prod("T37-3b", "3b", "per-period interest round-trip vs textbook balance x rateFactor",
                D_2024_01_01, D_2024_01_01, "13202", 6, "16.8", "MNT", "t37_3b"));
        // Second 3b shape, month-end seed 31 Jan, so the month-end re-anchor is exercised too.
        cases.add(prod("T37-3b-2", "3b", "round-trip separator on a 31-Jan month-end seed",
                LocalDate.of(2024, 1, 31), LocalDate.of(2024, 1, 31), "3924149", 6, "16.8", "MNT", "t37_3b_2"));

        // ---- ITEM 3c -- guard in the LATER-DISBURSEMENT window ----------------------------
        // Disbursement ON repayment period 1's due date, so |relatedRepaymentPeriods| = 5 while
        // NumberOfRepayments = 6.  Candidate named in DEC-1 section 8 item 3c.
        cases.add(prod("T37-3c", "3c", "later-disbursement guard; n=|related| vs n=NumberOfRepayments",
                D_2024_01_01, LocalDate.of(2024, 2, 1), "10548069", 6, "16.8", "MNT", "t37_3c"));
        cases.add(prod("T37-3c-2", "3c", "second later-disbursement separator at 21.6%",
                D_2024_01_01, LocalDate.of(2024, 2, 1), "13549647", 6, "21.6", "MNT", "t37_3c_2"));

        // ---- ITEM 3d -- disbursement STRICTLY INSIDE a repayment period -------------------
        // Two interest periods in repayment period 1, and the rate factor's day-count ratio
        // actualDaysInPeriod / calculatedDaysInPeriod is strictly less than 1 on the segment
        // carrying the balance.  Candidate named in DEC-1 section 8 item 3d.
        cases.add(prod("T37-3d", "3d", "disbursement 15 Jan, strictly inside repayment period 1",
                D_2024_01_01, LocalDate.of(2024, 1, 15), "1200000", 6, "21.6", "MNT", "t37_3d"));
        cases.add(prod("T37-3d-2", "3d", "strictly-inside disbursement on a 36-period schedule",
                D_2024_01_01, LocalDate.of(2024, 1, 20), "127704", 36, "16.8", "MNT", "t37_3d_2"));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"task\": \"T37\",\n");
        sb.append("  \"harness\": \"CaptureBinding.java\",\n");
        sb.append("  \"path\": \"A -- embeddable seam, in-process, no server, no database\",\n");
        sb.append("  \"fineractCommit\": \"426a23544e8426a38ae43ae404670a0a7e85b9eb\",\n");
        sb.append("  \"moneyHelperPrecisionConstant\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append("  \"javaVersion\": \"").append(System.getProperty("java.version")).append("\",\n");
        sb.append("  \"javaVmName\": \"").append(System.getProperty("java.vm.name")).append("\",\n");
        sb.append("  \"javaVmVersion\": \"").append(System.getProperty("java.vm.version")).append("\",\n");
        sb.append("  \"javaVendor\": \"").append(System.getProperty("java.vendor")).append("\",\n");
        sb.append("  \"jvmUserTimezone\": \"").append(System.getProperty("user.timezone")).append("\",\n");
        sb.append("  \"jvmFileEncoding\": \"").append(System.getProperty("file.encoding")).append("\",\n");
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
        b.append("      \"bindingItem\": \"").append(c.bindingItem()).append("\",\n");
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
