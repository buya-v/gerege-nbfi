/*
 * T23 RE-REVIEW PROBE — independent observation against the pinned reference oracle
 * (Fineract 426a23544e8426a38ae43ae404670a0a7e85b9eb, image
 * sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a), Path A seam.
 *
 * It asserts nothing and predicts nothing. Every line printed is what the oracle emitted or threw.
 *
 * Questions it settles, all of which DEC-1 revision 2 answers normatively:
 *
 *  Q1  A single disbursement dated ON OR AFTER the last repayment due date. DEC-1 §4.6 / Schedule's
 *      ordering rule says such a row "sorts after every repayment row" — which presupposes the row
 *      exists. The request is inside DEC-1's stated graded domain (nothing constrains the
 *      disbursement date relative to ScheduleStartDate).
 *  Q2  A single disbursement dated BEFORE ScheduleStartDate. Same graded-domain membership.
 *  Q3  FrequencyYears. DEC-1 §4.10 / RepaymentFrequencyUnit says the oracle "CANNOT answer it on this
 *      path" and throws (ProgressiveEMICalculator.java:1602-1610). That dispatch is only reached from
 *      the DAYS_30 arm (:1536). Probe both arms.
 *  Q4  Small principal on a long term at (19, HALF_UP) — the shape on which the EMI re-adjust loop's
 *      guard (EmiAdjustment.shouldBeAdjusted, EmiAdjustment.java:31-36) evaluates true, inside the
 *      graded domain. DEC-1 §4.3 says the loop "is reachable only outside the graded domain".
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

public class T23Probe {

    static void tenant(String id) {
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, id, id, "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(id, 4); // HALF_UP
    }

    static void run(String label, LocalDate start, LocalDate disb, BigDecimal principal, int n,
            BigDecimal rate, String freqType, DaysInMonthType dim, DaysInYearType diy) {
        System.out.println();
        System.out.println("### " + label);
        System.out.println("    start=" + start + " disb=" + disb + " P=" + principal + " n=" + n
                + " rate=" + rate + " freq=" + freqType + " dim=" + dim + " diy=" + diy);
        final MathContext mc = new MathContext(19, RoundingMode.HALF_UP);
        final CurrencyData currency = new CurrencyData("MNT", "MNT", 2, null, "MNT", "MNT");
        final LoanRepaymentScheduleModelData d = new LoanRepaymentScheduleModelData(start, currency, principal,
                disb, n, 1, freqType, rate, false, dim, diy, BigDecimal.ZERO, null, null, false, null,
                InterestMethod.DECLINING_BALANCE, true, false);
        try {
            LoanSchedulePlan plan = new EmbeddableProgressiveLoanScheduleGenerator().generate(mc, d);
            System.out.println("    OK  loanTermInDays=" + plan.getLoanTermInDays()
                    + " totalDisbursed=" + plan.getTotalDisbursedAmount()
                    + " totalInterest=" + plan.getTotalInterestAmount()
                    + " totalRepayment=" + plan.getTotalRepaymentAmount());
            int disbRows = 0, dpRows = 0, repRows = 0;
            for (LoanSchedulePlanPeriod p : plan.getPeriods()) {
                if (p instanceof LoanSchedulePlanDisbursementPeriod dp) {
                    disbRows++;
                    System.out.println("      DISBURSEMENT           due=" + dp.getPeriodDueDate()
                            + " principal=" + dp.getPrincipalAmount());
                } else if (p instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                    dpRows++;
                    System.out.println("      DOWNPAYMENT   #" + dpp.getPeriodNumber() + " due=" + dpp.getPeriodDueDate());
                } else if (p instanceof LoanSchedulePlanRepaymentPeriod rp) {
                    repRows++;
                    System.out.println("      REPAYMENT     #" + rp.getPeriodNumber()
                            + " from=" + rp.getPeriodFromDate() + " due=" + rp.getPeriodDueDate()
                            + " principal=" + rp.getPrincipalAmount() + " interest=" + rp.getInterestAmount()
                            + " total=" + rp.getTotalDueAmount()
                            + " balance=" + rp.getOutstandingLoanBalance());
                }
            }
            System.out.println("    rows: disbursement=" + disbRows + " downPayment=" + dpRows + " repayment=" + repRows);
        } catch (Throwable t) {
            System.out.println("    THREW " + t.getClass().getName() + ": " + t.getMessage());
        }
    }

    public static void main(String[] args) {
        tenant("t23_probe");
        System.out.println("MoneyHelper.PRECISION      = " + MoneyHelper.PRECISION);
        System.out.println("MoneyHelper.getMathContext = " + MoneyHelper.getMathContext());

        final BigDecimal P = new BigDecimal("1200000");
        final BigDecimal R = new BigDecimal("21.6");
        final LocalDate S = LocalDate.of(2024, 1, 1);

        // ---- Q0 control: the ordinary graded-domain case, and the P-03 ordering case ----
        run("Q0a CONTROL  disbursement on the schedule start (ordinary)", S, S, P, 6, R, "MONTHS",
                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        run("Q0b CONTROL  disbursement exactly on repayment 1's due date (DEC-1 §4.6 observed case)",
                S, LocalDate.of(2024, 2, 1), P, 6, R, "MONTHS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);

        // ---- Q1: disbursement on / after the LAST due date. Last due date = 2024-07-01. ----
        run("Q1a  disbursement EXACTLY on the last repayment due date (2024-07-01)",
                S, LocalDate.of(2024, 7, 1), P, 6, R, "MONTHS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        run("Q1b  disbursement AFTER the last repayment due date (2024-09-01)",
                S, LocalDate.of(2024, 9, 1), P, 6, R, "MONTHS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);

        // ---- Q2: disbursement BEFORE the schedule start ----
        run("Q2   disbursement BEFORE the schedule start (2023-11-15)",
                S, LocalDate.of(2023, 11, 15), P, 6, R, "MONTHS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);

        // ---- Q3: YEARS on both day-count arms ----
        run("Q3a  RepaymentFrequencyUnit=YEARS on the 30/360 arm (DAYS_30)",
                S, S, P, 3, R, "YEARS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        run("Q3b  RepaymentFrequencyUnit=YEARS on the ACTUAL/ACTUAL arm",
                S, S, P, 3, R, "YEARS", DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL);
        run("Q3c  RepaymentFrequencyUnit=DAYS on the 30/360 arm (contract says computable)",
                S, S, P, 6, R, "DAYS", DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);

        // ---- Q4: small principal, long term — EmiAdjustment.shouldBeAdjusted territory ----
        run("Q4a  principal 4.00, 36 x 16.8% at (19, HALF_UP) — in the graded domain",
                S, S, new BigDecimal("4"), 36, new BigDecimal("16.8"), "MONTHS",
                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
        run("Q4b  principal 1.00, 36 x 16.8% at (19, HALF_UP) — in the graded domain",
                S, S, new BigDecimal("1"), 36, new BigDecimal("16.8"), "MONTHS",
                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360);
    }
}
