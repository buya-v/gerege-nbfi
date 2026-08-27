/*
 * T42 capture 2 -- two follow-ups the first capture opened.
 *
 * Same pinned oracle, same Path A seam, same rules: nothing asserted, nothing predicted, every
 * printed value is what the oracle emitted, BigDecimal.toPlainString(), no float anywhere.
 *
 * (1) THE PRECISION THRESHOLD.  Capture 1 found that threaded precision 19 DOES separate from
 *     12 -- contrary to T39 N-4's coverage statement -- but the coarse decade sweep only
 *     brackets the boundary.  This run bisects it, so the answer is "the smallest observed
 *     separating shape is X", not "somewhere between 5e7 and 1e9".
 *
 * (2) THE PATH B WIRING RULE, OBSERVED.  On the running server the threaded MathContext is not
 *     independent of the ambient one: the production caller reads the ambient context and
 *     hands it straight to the generator --
 *         LoanScheduleAssembler.java:753   final MathContext mc = MoneyHelper.getMathContext();
 *         LoanScheduleAssembler.java:765   loanScheduleGenerator.generate(mc, ...)
 *     (also :777, :797 and LoanScheduleGeneratorServiceImpl.java:44).
 *     The PB cases below reproduce that wiring EXACTLY -- they pass MoneyHelper.getMathContext()
 *     as the mc instead of constructing one -- and vary ONLY the tenant rounding ordinal.  If
 *     the money moves, the ambient reading is evidence about the arithmetic on that wiring, and
 *     the observation says so rather than the source comment saying so.
 *     The PA-control cases are the same shapes with an INDEPENDENTLY constructed mc, i.e. the
 *     Path A wiring, so the two wirings are compared side by side in one payload.
 */
import org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant;
import org.apache.fineract.infrastructure.core.service.ThreadLocalContextUtil;
import org.apache.fineract.organisation.monetary.data.CurrencyData;
import org.apache.fineract.organisation.monetary.domain.MoneyHelper;
import org.apache.fineract.portfolio.common.domain.DaysInMonthType;
import org.apache.fineract.portfolio.common.domain.DaysInYearType;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlan;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDisbursementPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDownPaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanRepaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class CaptureMathContext2 {

    /** How the MathContext handed to the generator is obtained. */
    enum Wiring {
        /** Path A: the caller constructs its own MathContext, independent of MoneyHelper. */
        PATH_A_INDEPENDENT_MC,
        /** Path B: the caller reads MoneyHelper.getMathContext() [LoanScheduleAssembler.java:753]. */
        PATH_B_AMBIENT_SOURCED_MC
    }

    record Case(String id, String family, String purpose, LocalDate startDate, LocalDate disbursementDate,
            BigDecimal principal, int noRepayments, BigDecimal annualRate, Wiring wiring, Integer precision,
            RoundingMode mode, int tenantRoundingMode) {
    }

    static Case prec(String id, String principal, int n, String rate, int precision) {
        return new Case(id, "PRECISION", "principal " + principal + ", n=" + n + ", rate " + rate
                + ", threaded (" + precision + ", HALF_UP), ambient HALF_UP(4)", LocalDate.of(2024, 1, 1),
                LocalDate.of(2024, 1, 1), new BigDecimal(principal), n, new BigDecimal(rate),
                Wiring.PATH_A_INDEPENDENT_MC, precision, RoundingMode.HALF_UP, 4);
    }

    static List<Case> cases() {
        final List<Case> cases = new ArrayList<>();

        // ---- (1) BISECT THE PRECISION-19-vs-12 THRESHOLD -------------------------------
        // Capture 1 bracketed it: at n=360 rate 7.7 it separates at principal 1e9 and not at
        // 5e7; at n=36 rate 13 it separates at 1e10 and not at 1e9; at n=6 rate 21.6 it
        // separates at 1e12 and not at 1e11.  Bisect all three brackets.
        final String[][] sweeps = {
                // { term, rate, principal ... }
                { "360", "7.7", "1200000", "2000000", "3000000", "5000000", "8000000", "10000000", "15000000",
                        "20000000", "25000000", "30000000", "40000000", "50000000", "60000000", "70000000",
                        "80000000", "100000000", "150000000", "200000000", "300000000", "400000000", "500000000",
                        "700000000", "900000000", "1000000000" },
                // the same magnitude ladder at two other rates, so "does it separate at MNT X"
                // is not answered from a single rate
                { "360", "21.6", "1200000", "3000000", "5000000", "10000000", "20000000", "30000000", "50000000",
                        "80000000", "100000000" },
                { "120", "13", "1200000", "5000000", "10000000", "20000000", "50000000", "100000000", "200000000",
                        "500000000", "1000000000" },
                { "36", "13", "1000000000", "2000000000", "3000000000", "4000000000", "5000000000", "6000000000",
                        "7000000000", "8000000000", "9000000000", "10000000000" },
                { "6", "21.6", "100000000000", "200000000000", "300000000000", "400000000000", "500000000000",
                        "600000000000", "700000000000", "800000000000", "900000000000", "1000000000000" }, };
        int k = 0;
        for (String[] sweep : sweeps) {
            final int n = Integer.parseInt(sweep[0]);
            final String rate = sweep[1];
            for (int i = 2; i < sweep.length; i++) {
                final String id = String.format("T42B-PREC-%02d", k++);
                cases.add(prec(id + "-p19", sweep[i], n, rate, 19));
                cases.add(prec(id + "-p12", sweep[i], n, rate, 12));
            }
        }

        // ---- (2) THE TWO WIRINGS, SIDE BY SIDE ------------------------------------------
        // Same shape, same tenant ordinals; only the WIRING differs.  Path A constructs its own
        // (19, HALF_UP); Path B reads MoneyHelper.getMathContext(), which the ordinal moves.
        final int[] ordinals = { 4, 1, 0, 6 }; // HALF_UP, DOWN, UP, HALF_EVEN
        for (int ord : ordinals) {
            cases.add(new Case("T42B-PA-ord" + ord, "WIRING",
                    "PATH A wiring: caller constructs (19, HALF_UP) itself; tenant ordinal " + ord,
                    LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1200000"), 6,
                    new BigDecimal("21.6"), Wiring.PATH_A_INDEPENDENT_MC, 19, RoundingMode.HALF_UP, ord));
            cases.add(new Case("T42B-PB-ord" + ord, "WIRING",
                    "PATH B wiring: caller passes MoneyHelper.getMathContext() as mc "
                            + "[LoanScheduleAssembler.java:753]; tenant ordinal " + ord,
                    LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1200000"), 6,
                    new BigDecimal("21.6"), Wiring.PATH_B_AMBIENT_SOURCED_MC, null, null, ord));
        }
        // the half-cent tie T36 used as its Path B behavioural canary: 1,162,502.50 x 0.018 =
        // 20,925.045.  Same shape under both wirings, all four ordinals.
        for (int ord : ordinals) {
            cases.add(new Case("T42B-PA-tie-ord" + ord, "WIRING",
                    "PATH A wiring, T36's half-cent tie shape (1,162,502.50 x 0.018 = 20,925.045); ordinal " + ord,
                    LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1162502.50"), 12,
                    new BigDecimal("21.6"), Wiring.PATH_A_INDEPENDENT_MC, 19, RoundingMode.HALF_UP, ord));
            cases.add(new Case("T42B-PB-tie-ord" + ord, "WIRING",
                    "PATH B wiring, T36's half-cent tie shape; ordinal " + ord, LocalDate.of(2024, 1, 1),
                    LocalDate.of(2024, 1, 1), new BigDecimal("1162502.50"), 12, new BigDecimal("21.6"),
                    Wiring.PATH_B_AMBIENT_SOURCED_MC, null, null, ord));
        }

        return cases;
    }

    public static void main(String[] args) {
        final List<Case> cases = cases();
        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"task\": \"T42\",\n");
        sb.append("  \"harness\": \"CaptureMathContext2.java\",\n");
        sb.append("  \"question\": \"T42(b) precision threshold bisection; and the Path A vs Path B MathContext WIRING, observed side by side\",\n");
        sb.append("  \"path\": \"A -- embeddable seam, in-process, no server, no database.  The PATH_B_AMBIENT_SOURCED_MC cases reproduce Path B's WIRING (LoanScheduleAssembler.java:753), not Path B's transport.\",\n");
        sb.append("  \"fineractCommit\": \"426a23544e8426a38ae43ae404670a0a7e85b9eb\",\n");
        sb.append("  \"moneyHelperPrecisionConstant\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append("  \"javaVersion\": \"").append(System.getProperty("java.version")).append("\",\n");
        sb.append("  \"javaVmVersion\": \"").append(System.getProperty("java.vm.version")).append("\",\n");
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
        final String tenantId = "t42b_" + c.id().toLowerCase().replace('-', '_');
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenantId, tenantId, "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(tenantId, c.tenantRoundingMode());
        final String ambient = String.valueOf(MoneyHelper.getMathContext());

        // THE ONLY DIFFERENCE BETWEEN THE TWO WIRINGS.
        //
        // NEGATIVE-TEST HOOK, never set on a capture run.  -Dt42.breakWiring=true makes the
        // PATH B cases construct their own MathContext instead of sourcing it from MoneyHelper,
        // i.e. it silently turns them into Path A cases.  run-mathcontext2.sh's assertion 5
        // ("a PATH B case's effective mc must EQUAL the ambient reading") must then FAIL.  An
        // assertion suite that has never failed has not been tested (.softhouse/patterns.md).
        final boolean breakWiring = Boolean.getBoolean("t42.breakWiring");
        final MathContext mc = switch (c.wiring()) {
            case PATH_A_INDEPENDENT_MC -> new MathContext(c.precision(), c.mode());
            case PATH_B_AMBIENT_SOURCED_MC ->
                breakWiring ? new MathContext(19, RoundingMode.HALF_UP) : MoneyHelper.getMathContext();
        };

        final EmbeddableProgressiveLoanScheduleGenerator generator = new EmbeddableProgressiveLoanScheduleGenerator();
        final CurrencyData currency = new CurrencyData("MNT", "MNT", 2, null, "MNT", "MNT");
        final LoanRepaymentScheduleModelData config = new LoanRepaymentScheduleModelData(c.startDate(), currency,
                c.principal(), c.disbursementDate(), c.noRepayments(), 1, "MONTHS", c.annualRate(), false,
                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, BigDecimal.ZERO, null, null, false, null,
                InterestMethod.DECLINING_BALANCE, true, false);

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"family\": \"").append(c.family()).append("\",\n");
        b.append("      \"purpose\": \"").append(c.purpose()).append("\",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"wiring\": \"").append(c.wiring()).append("\",\n");
        b.append("        \"scheduleGenerationStartDate\": \"").append(c.startDate()).append("\",\n");
        b.append("        \"disbursementDate\": \"").append(c.disbursementDate()).append("\",\n");
        b.append("        \"disbursementAmount\": \"").append(c.principal().toPlainString()).append("\",\n");
        b.append("        \"numberOfRepayments\": ").append(c.noRepayments()).append(",\n");
        b.append("        \"annualNominalInterestRate\": \"").append(c.annualRate().toPlainString()).append("\",\n");
        b.append("        \"tenantId\": \"").append(tenantId).append("\",\n");
        b.append("        \"tenantRoundingModeOrdinal\": ").append(c.tenantRoundingMode()).append(",\n");
        b.append("        \"ambientMoneyHelperMathContext\": \"").append(ambient).append("\",\n");
        // the mc ACTUALLY handed to the generator, echoed from the object itself
        b.append("        \"effectiveThreadedMathContext\": \"").append(mc).append("\",\n");
        b.append("        \"threadedMathContextPrecision\": ").append(mc.getPrecision()).append(",\n");
        b.append("        \"threadedMathContextRoundingMode\": \"").append(mc.getRoundingMode()).append("\",\n");
        b.append("        \"currencyCode\": \"MNT\",\n");
        b.append("        \"currencyDecimalPlaces\": 2,\n");
        b.append("        \"currencyInMultiplesOf\": null,\n");
        b.append("        \"daysInMonth\": \"DAYS_30\",\n");
        b.append("        \"daysInYear\": \"DAYS_360\",\n");
        b.append("        \"interestMethod\": \"DECLINING_BALANCE\"\n");
        b.append("      },\n");

        final LoanSchedulePlan plan;
        try {
            plan = generator.generate(mc, config);
        } catch (RuntimeException e) {
            final StringWriter sw = new StringWriter();
            e.printStackTrace(new PrintWriter(sw));
            b.append("      \"observed\": null,\n");
            b.append("      \"error\": \"").append(e.getClass().getName()).append(": ")
                    .append(String.valueOf(e.getMessage()).replace("\\", "\\\\").replace("\"", "'").replace("\n", " "))
                    .append("\"\n");
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

    static String pl(final BigDecimal v) {
        return v == null ? "null" : v.toPlainString();
    }
}
