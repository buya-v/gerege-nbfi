/*
 * T24 PROBE — observations against the pinned reference oracle (Fineract
 * 426a23544e8426a38ae43ae404670a0a7e85b9eb, image
 * sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a), Path A
 * (fineract-progressive-loan-embeddable-schedule-generator), in-process, no server, no database.
 *
 * It asserts nothing and predicts nothing. Every line printed is what the oracle emitted or threw.
 * The MathContext and the tenant rounding mode are READ BACK from MoneyHelper at capture time and
 * printed, never assumed.
 *
 * Sections, each answering one P0 of .softhouse/reviews/T23-DEC-1-v2-rereview.md §10:
 *
 *  L-*  P0-1. The EMI re-adjust loop (ProgressiveEMICalculator.java:1258-1308, called at :749).
 *       Twelve requests, all inside DEC-1 revision 2's stated graded domain (one disbursement on
 *       the schedule start, RepaymentEvery 1, MONTHS, DECLINING_BALANCE, DAYS_30/DAYS_360, no down
 *       payment, installmentAmountInMultiplesOf null, MNT with 2 decimal places), chosen to sit on
 *       three different exits of the loop. Which exit each takes is NOT asserted here; it is
 *       decided by comparing this raw output against t24_rederive_with_loop.py.
 *
 *  W-*  P0-2. The disbursement window. One disbursement, varied against
 *       [ScheduleStartDate, last repayment due date). Six monthly periods from 2024-01-01, so the
 *       due dates are 2024-02-01 .. 2024-07-01.
 *
 *  Y-*  P0-3. RepaymentFrequencyUnit = YEARS on each day-count arm, plus DAYS and WEEKS for
 *       comparison.
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

import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;

public class T24Probe {

    static final LocalDate S = LocalDate.of(2024, 1, 1);
    static final CurrencyData MNT = new CurrencyData("MNT", "MNT", 2, null, "MNT", "MNT");

    static LoanRepaymentScheduleModelData data(LocalDate start, LocalDate disb, String principal, int n,
            String rate, String freq, DaysInMonthType dim, DaysInYearType diy) {
        return new LoanRepaymentScheduleModelData(start, MNT, new BigDecimal(principal), disb, n, 1, freq,
                new BigDecimal(rate), false, dim, diy, BigDecimal.ZERO, null, null, false, null,
                InterestMethod.DECLINING_BALANCE, true, false);
    }

    /** Compact one-line form, for the L-* cases: comparable field-by-field with the re-derivation. */
    static void compact(String id, String principal, int n, String rate) {
        final MathContext mc = new MathContext(19, RoundingMode.HALF_UP);
        LoanSchedulePlan plan = new EmbeddableProgressiveLoanScheduleGenerator()
                .generate(mc, data(S, S, principal, n, rate, "MONTHS", DaysInMonthType.DAYS_30,
                        DaysInYearType.DAYS_360));
        StringBuilder b = new StringBuilder();
        b.append(id).append(" CASE P=").append(principal).append(" n=").append(n).append(" rate=").append(rate)
                .append(" totalInterest=").append(plan.getTotalInterestAmount())
                .append(" totalRepayment=").append(plan.getTotalRepaymentAmount()).append(" |");
        for (LoanSchedulePlanPeriod q : plan.getPeriods()) {
            if (q instanceof LoanSchedulePlanRepaymentPeriod rp) {
                b.append(" #").append(rp.getPeriodNumber()).append(":").append(rp.getPrincipalAmount())
                        .append("/").append(rp.getInterestAmount()).append("/").append(rp.getTotalDueAmount())
                        .append("/").append(rp.getOutstandingLoanBalance());
            }
        }
        System.out.println(b);
    }

    /** Full row dump, for the W-* and Y-* cases: row kinds and emission order are the observation. */
    static void full(String id, String label, LocalDate start, LocalDate disb, String principal, int n,
            String rate, String freq, DaysInMonthType dim, DaysInYearType diy) {
        System.out.println();
        System.out.println("### " + id + "  " + label);
        System.out.println("    start=" + start + " disb=" + disb + " P=" + principal + " n=" + n + " rate=" + rate
                + " freq=" + freq + " dim=" + dim + " diy=" + diy);
        final MathContext mc = new MathContext(19, RoundingMode.HALF_UP);
        try {
            LoanSchedulePlan plan = new EmbeddableProgressiveLoanScheduleGenerator()
                    .generate(mc, data(start, disb, principal, n, rate, freq, dim, diy));
            System.out.println("    OK  loanTermInDays=" + plan.getLoanTermInDays()
                    + " totalDisbursed=" + plan.getTotalDisbursedAmount()
                    + " totalPrincipal=" + plan.getTotalPrincipalAmount()
                    + " totalInterest=" + plan.getTotalInterestAmount()
                    + " totalRepayment=" + plan.getTotalRepaymentAmount());
            int disbRows = 0, dpRows = 0, repRows = 0, order = 0;
            for (LoanSchedulePlanPeriod p : plan.getPeriods()) {
                order++;
                if (p instanceof LoanSchedulePlanDisbursementPeriod dp) {
                    disbRows++;
                    System.out.println("      [" + order + "] DISBURSEMENT  due=" + dp.getPeriodDueDate()
                            + " principal=" + dp.getPrincipalAmount());
                } else if (p instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                    dpRows++;
                    System.out.println("      [" + order + "] DOWNPAYMENT   #" + dpp.getPeriodNumber()
                            + " due=" + dpp.getPeriodDueDate() + " principal=" + dpp.getPrincipalAmount());
                } else if (p instanceof LoanSchedulePlanRepaymentPeriod rp) {
                    repRows++;
                    System.out.println("      [" + order + "] REPAYMENT     #" + rp.getPeriodNumber()
                            + " from=" + rp.getPeriodFromDate() + " due=" + rp.getPeriodDueDate()
                            + " principal=" + rp.getPrincipalAmount() + " interest=" + rp.getInterestAmount()
                            + " total=" + rp.getTotalDueAmount() + " balance=" + rp.getOutstandingLoanBalance());
                }
            }
            System.out.println("    rows: disbursement=" + disbRows + " downPayment=" + dpRows
                    + " repayment=" + repRows);
        } catch (Throwable t) {
            System.out.println("    THREW " + t.getClass().getName() + ": " + t.getMessage());
        }
    }

    public static void main(String[] args) {
        final String tenant = "t24_probe";
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenant, tenant, "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(tenant, 4); // 4 = HALF_UP, the ratified Gerege mode

        System.out.println("PINNED_COMMIT              = 426a23544e8426a38ae43ae404670a0a7e85b9eb");
        System.out.println("MoneyHelper.PRECISION      = " + MoneyHelper.PRECISION);
        System.out.println("MoneyHelper.getMathContext = " + MoneyHelper.getMathContext());
        System.out.println("MoneyHelper.getRoundingMode= " + MoneyHelper.getRoundingMode());
        System.out.println("threaded MathContext       = " + new MathContext(19, RoundingMode.HALF_UP));
        System.out.println("currency                   = MNT decimalPlaces=2 inMultiplesOf=null");
        System.out.println();
        System.out.println("== L: EMI re-adjust loop, inside DEC-1 rev-2's stated graded domain ==");

        compact("L-01", "1000000", 6, "21.6");
        compact("L-02", "1000000", 36, "16.8");
        compact("L-03", "1200000", 36, "16.8");
        compact("L-04", "1400000", 18, "18.5");
        compact("L-05", "1500000", 12, "21.6");
        compact("L-06", "2400000", 6, "21.6");
        compact("L-07", "2450000", 18, "18.5");
        compact("L-08", "2350000", 36, "16.8");
        compact("L-09", "4100000", 12, "21.6");
        compact("L-10", "6250000", 24, "16.8");
        compact("L-11", "1014632", 6, "7.0");
        compact("L-12", "1000", 18, "18.5");

        System.out.println();
        System.out.println("== W: the disbursement window. due dates are 2024-02-01 .. 2024-07-01 ==");

        full("W-01", "disbursement one day BEFORE ScheduleStartDate", S, LocalDate.of(2023, 12, 31),
                "1200000", 6, "21.6", "MONTHS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        full("W-02", "disbursement EXACTLY on ScheduleStartDate", S, S,
                "1200000", 6, "21.6", "MONTHS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        full("W-03", "disbursement one day AFTER ScheduleStartDate (inside period 1)", S, LocalDate.of(2024, 1, 2),
                "1200000", 6, "21.6", "MONTHS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        full("W-04", "disbursement EXACTLY on repayment 1's due date (inside period 2's window)", S,
                LocalDate.of(2024, 2, 1), "1200000", 6, "21.6", "MONTHS", DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360);
        full("W-05", "disbursement one day BEFORE the last due date (inside period 6's window)", S,
                LocalDate.of(2024, 6, 30), "1200000", 6, "21.6", "MONTHS", DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360);
        full("W-06", "disbursement EXACTLY on the last repayment due date", S, LocalDate.of(2024, 7, 1),
                "1200000", 6, "21.6", "MONTHS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        full("W-07", "disbursement AFTER the last repayment due date", S, LocalDate.of(2024, 8, 1),
                "1200000", 6, "21.6", "MONTHS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);

        System.out.println();
        System.out.println("== Y: repayment frequency unit against the day-count arm ==");

        full("Y-01", "YEARS on the fixed 30/360 arm", S, S, "1200000", 3, "21.6", "YEARS",
                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        full("Y-02", "YEARS on the ACTUAL/ACTUAL arm", S, S, "1200000", 3, "21.6", "YEARS",
                DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL);
        full("Y-03", "MONTHS on the ACTUAL/ACTUAL arm (control for Y-02)", S, S, "1200000", 6, "21.6", "MONTHS",
                DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL);
        full("Y-04", "DAYS on the fixed 30/360 arm", S, S, "1200000", 6, "21.6", "DAYS",
                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        full("Y-05", "WEEKS on the fixed 30/360 arm", S, S, "1200000", 6, "21.6", "WEEKS",
                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        full("Y-06", "YEARS on the DAYS_30 / ACTUAL mix", S, S, "1200000", 3, "21.6", "YEARS",
                DaysInMonthType.DAYS_30, DaysInYearType.ACTUAL);
        full("Y-07", "YEARS on the ACTUAL / DAYS_360 mix", S, S, "1200000", 3, "21.6", "YEARS",
                DaysInMonthType.ACTUAL, DaysInYearType.DAYS_360);
    }
}
