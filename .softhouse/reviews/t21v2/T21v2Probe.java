/*
 * T21-v2 AUDIT PROBE — runs against the PINNED reference oracle (Fineract commit
 * 426a23544e8426a38ae43ae404670a0a7e85b9eb, image
 * sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a) through the same
 * Path A embeddable seam the capture harness uses.
 *
 * It asserts nothing and predicts nothing. Every value printed is what the oracle emitted.
 * Its job is to turn three MODEL-located claims into OBSERVATIONS:
 *
 *   A. the "precision is load-bearing only above a size threshold" claim in PASS3-REPORT.md —
 *      by running the p12/p19 pair at principals my model flags as divergent, INCLUDING a tiny one;
 *   B. installmentAmountInMultiplesOf at the ratified production MathContext (19, HALF_UP);
 *   C. daysInYearCustomStrategy at the ratified production MathContext (19, HALF_UP).
 *
 * B and C are also probed REFLECTIVELY through the seam's own assembly path
 * (LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)) so the
 * differential result has a stated mechanism rather than an inferred one.
 *
 * Every case sets a distinct tenant with rounding mode HALF_UP(4), so the ambient
 * MoneyHelper context is (19, HALF_UP), matching production.
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
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanRepaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanApplicationTerms;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.lang.reflect.Field;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;

public class T21v2Probe {

    static final LocalDate D = LocalDate.of(2024, 1, 1);
    static int tenantSeq = 0;

    static void tenant() {
        String id = "t21v2_" + (tenantSeq++);
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, id, id, "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(id, 4); // HALF_UP
    }

    static LoanRepaymentScheduleModelData model(LocalDate start, LocalDate disb, BigDecimal principal, int n,
            BigDecimal rate, String ccy, int digits, Integer inMultiplesOf, Integer installmentMultiplesOf,
            DaysInMonthType dim, DaysInYearType diy, DaysInYearCustomStrategyType diyCustom) {
        CurrencyData currency = new CurrencyData(ccy, ccy, digits, inMultiplesOf, ccy, ccy);
        return new LoanRepaymentScheduleModelData(start, currency, principal, disb, n, 1, "MONTHS", rate, false, dim,
                diy, BigDecimal.ZERO, installmentMultiplesOf, null, false, diyCustom, InterestMethod.DECLINING_BALANCE,
                true, false);
    }

    static String render(LoanSchedulePlan plan) {
        StringBuilder b = new StringBuilder();
        b.append("term=").append(plan.getLoanTermInDays()).append(" disb=").append(plan.getTotalDisbursedAmount())
                .append(" int=").append(plan.getTotalInterestAmount()).append(" rep=")
                .append(plan.getTotalRepaymentAmount()).append("\n");
        for (LoanSchedulePlanPeriod p : plan.getPeriods()) {
            if (p instanceof LoanSchedulePlanDisbursementPeriod dp) {
                b.append("      DISB ").append(dp.periodDueDate()).append(" ").append(dp.getPrincipalAmount())
                        .append("\n");
            } else if (p instanceof LoanSchedulePlanRepaymentPeriod rp) {
                b.append("      REP  #").append(rp.periodNumber()).append(" from=").append(rp.periodFromDate())
                        .append(" due=").append(rp.periodDueDate()).append(" prin=").append(rp.getPrincipalAmount())
                        .append(" int=").append(rp.getInterestAmount()).append(" fee=").append(rp.getFeeAmount())
                        .append(" pen=").append(rp.getPenaltyAmount()).append(" tot=").append(rp.getTotalDueAmount())
                        .append(" bal=").append(rp.getOutstandingLoanBalance()).append(" totOut=")
                        .append(rp.getTotalOutstandingLoanBalance()).append("\n");
            }
        }
        return b.toString();
    }

    static String run(MathContext mc, LoanRepaymentScheduleModelData m) {
        tenant();
        try {
            return render(new EmbeddableProgressiveLoanScheduleGenerator().generate(mc, m));
        } catch (RuntimeException e) {
            java.io.StringWriter sw = new java.io.StringWriter();
            e.printStackTrace(new java.io.PrintWriter(sw));
            return "EXCEPTION\n" + sw;
        }
    }

    static void pair(String label, MathContext a, MathContext b, LoanRepaymentScheduleModelData ma,
            LoanRepaymentScheduleModelData mb) {
        String ra = run(a, ma);
        String rb = run(b, mb);
        System.out.println("### " + label);
        System.out.println("  A: " + ra.replace("\n", "\n  "));
        System.out.println("  B: " + rb.replace("\n", "\n  "));
        System.out.println("  ==> " + (ra.equals(rb) ? "IDENTICAL" : "DIFFERENT"));
        System.out.println();
    }

    static Object reflect(LoanApplicationTerms t, String field) {
        try {
            Field f = LoanApplicationTerms.class.getDeclaredField(field);
            f.setAccessible(true);
            return f.get(t);
        } catch (ReflectiveOperationException e) {
            return "REFLECTION FAILED: " + e;
        }
    }

    public static void main(String[] args) {
        final MathContext P19 = new MathContext(19, RoundingMode.HALF_UP);
        final MathContext P12 = new MathContext(12, RoundingMode.HALF_UP);

        System.out.println("MoneyHelper.PRECISION = " + MoneyHelper.PRECISION);
        tenant();
        System.out.println("ambient MoneyHelper MathContext = " + MoneyHelper.getMathContext());
        System.out.println();

        // ---- A. the size-threshold claim -----------------------------------------------------
        System.out.println("======== A. precision 12 vs 19, small principals, 36 x 16.8% ========");
        for (String p : new String[] { "1", "2", "3", "4", "5", "59", "100", "6940" }) {
            pair("36 x 16.8%  principal " + p + "   p12 vs p19", P12, P19,
                    model(D, D, new BigDecimal(p), 36, new BigDecimal("16.8"), "MNT", 2, null, null,
                            DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null),
                    model(D, D, new BigDecimal(p), 36, new BigDecimal("16.8"), "MNT", 2, null, null,
                            DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null));
        }
        System.out.println("======== A2. the same probe on the C-00 shape, 6 x 7.0% ========");
        for (String p : new String[] { "4", "100", "43811" }) {
            pair("6 x 7.0%  principal " + p + "   p12 vs p19", P12, P19,
                    model(D, D, new BigDecimal(p), 6, new BigDecimal("7.0"), "usd", 2, null, null,
                            DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null),
                    model(D, D, new BigDecimal(p), 6, new BigDecimal("7.0"), "usd", 2, null, null,
                            DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null));
        }

        // ---- B. installmentAmountInMultiplesOf at (19, HALF_UP) --------------------------------
        System.out.println("======== B. installmentAmountInMultiplesOf at PRODUCTION (19, HALF_UP) ========");
        pair("MNT 50,000,000 / 36 x 16.8%   installmentMultiplesOf null vs 100", P19, P19,
                model(D, D, new BigDecimal("50000000"), 36, new BigDecimal("16.8"), "MNT", 2, null, null,
                        DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null),
                model(D, D, new BigDecimal("50000000"), 36, new BigDecimal("16.8"), "MNT", 2, null, 100,
                        DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null));
        pair("MNT 50,000,000 / 36 x 16.8%   installmentMultiplesOf null vs 100000", P19, P19,
                model(D, D, new BigDecimal("50000000"), 36, new BigDecimal("16.8"), "MNT", 2, null, null,
                        DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null),
                model(D, D, new BigDecimal("50000000"), 36, new BigDecimal("16.8"), "MNT", 2, null, 100000,
                        DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null));
        pair("MNT 5,000,000 / 18 x 18.5%   currency inMultiplesOf null vs 100 at decimalPlaces 0", P19, P19,
                model(D, D, new BigDecimal("5000000"), 18, new BigDecimal("18.5"), "MNT", 0, null, null,
                        DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null),
                model(D, D, new BigDecimal("5000000"), 18, new BigDecimal("18.5"), "MNT", 0, 100, null,
                        DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null));

        // ---- C. daysInYearCustomStrategy at (19, HALF_UP) ---------------------------------------
        System.out.println("======== C. daysInYearCustomStrategy at PRODUCTION (19, HALF_UP), ACTUAL/ACTUAL over leap 2024 ========");
        pair("ACTUAL/ACTUAL 2024   custom null vs FULL_LEAP_YEAR", P19, P19,
                model(D, D, new BigDecimal("50000000"), 18, new BigDecimal("16.8"), "MNT", 2, null, null,
                        DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL, null),
                model(D, D, new BigDecimal("50000000"), 18, new BigDecimal("16.8"), "MNT", 2, null, null,
                        DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL, DaysInYearCustomStrategyType.FULL_LEAP_YEAR));
        pair("ACTUAL/ACTUAL 2024   custom null vs FEB_29_PERIOD_ONLY", P19, P19,
                model(D, D, new BigDecimal("50000000"), 18, new BigDecimal("16.8"), "MNT", 2, null, null,
                        DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL, null),
                model(D, D, new BigDecimal("50000000"), 18, new BigDecimal("16.8"), "MNT", 2, null, null,
                        DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL, DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY));

        // ---- D. reflective mechanism ------------------------------------------------------------
        System.out.println("======== D. what the seam's own assembly path actually stores ========");
        tenant();
        LoanRepaymentScheduleModelData m = model(D, D, new BigDecimal("50000000"), 36, new BigDecimal("16.8"), "MNT", 2,
                777, 999, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, DaysInYearCustomStrategyType.FULL_LEAP_YEAR);
        System.out.println("  modelData.installmentAmountInMultiplesOf() = " + m.installmentAmountInMultiplesOf());
        System.out.println("  modelData.daysInYearCustomStrategy()       = " + m.daysInYearCustomStrategy());
        System.out.println("  modelData.currency().getInMultiplesOf()    = " + m.currency().getInMultiplesOf());
        LoanApplicationTerms terms = LoanApplicationTerms.assembleFrom(m, P19);
        System.out.println("  terms.installmentAmountInMultiplesOf (reflected) = "
                + reflect(terms, "installmentAmountInMultiplesOf"));
        System.out.println("  terms.daysInYearCustomStrategy       (reflected) = "
                + reflect(terms, "daysInYearCustomStrategy"));
        System.out.println("  terms.getInstallmentAmountInMultiplesOf()        = " + terms.getInstallmentAmountInMultiplesOf());
        System.out.println("  terms.toLoanConfigurationDetails().getDaysInYearCustomStrategy() = " + terms.toLoanConfigurationDetails().getDaysInYearCustomStrategy());
        System.out.println("  terms.getSeedDate()                              = " + terms.getSeedDate());

        // ---- E. columns the harness never emits --------------------------------------------------
        System.out.println();
        System.out.println("======== E. per-period columns available but never emitted by Capture3 ========");
        tenant();
        LoanSchedulePlan plan = new EmbeddableProgressiveLoanScheduleGenerator().generate(P19,
                model(D, D, BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), "usd", 2, null, null,
                        DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null));
        System.out.println("  plan.totalPrincipalAmount = " + plan.getTotalPrincipalAmount());
        System.out.println("  plan.totalFeeAmount       = " + plan.getTotalFeeAmount());
        System.out.println("  plan.totalPenaltyAmount   = " + plan.getTotalPenaltyAmount());
        System.out.println("  plan.totalOutstandingAmount = " + plan.getTotalOutstandingAmount());
        System.out.println(render(plan));
    }
}
