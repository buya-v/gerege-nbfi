/*
 * T23 RE-REVIEW PROBE 2 — put the EMI-re-adjust-guard candidates to the pinned oracle (Path A seam)
 * at the PRODUCTION MathContext (19, HALF_UP), tenant rounding mode HALF_UP(4).
 *
 * Every candidate is inside DEC-1 revision 2's stated graded domain: one disbursement on the
 * schedule start, RepaymentEvery 1, MONTHS, DECLINING_BALANCE, DAYS_30/DAYS_360, no down payment,
 * installmentAmountInMultiplesOf null, currency decimals 2.
 *
 * Prints only observed output. Nothing is asserted here.
 */
import org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant;
import org.apache.fineract.infrastructure.core.service.ThreadLocalContextUtil;
import org.apache.fineract.organisation.monetary.data.CurrencyData;
import org.apache.fineract.organisation.monetary.domain.MoneyHelper;
import org.apache.fineract.portfolio.common.domain.DaysInMonthType;
import org.apache.fineract.portfolio.common.domain.DaysInYearType;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlan;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanRepaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;

public class T23Probe2 {

    static void one(String p, int n, String rate) {
        final MathContext mc = new MathContext(19, RoundingMode.HALF_UP);
        final CurrencyData currency = new CurrencyData("MNT", "MNT", 2, null, "MNT", "MNT");
        final LocalDate s = LocalDate.of(2024, 1, 1);
        final LoanRepaymentScheduleModelData d = new LoanRepaymentScheduleModelData(s, currency,
                new BigDecimal(p), s, n, 1, "MONTHS", new BigDecimal(rate), false,
                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, BigDecimal.ZERO, null, null, false, null,
                InterestMethod.DECLINING_BALANCE, true, false);
        LoanSchedulePlan plan = new EmbeddableProgressiveLoanScheduleGenerator().generate(mc, d);
        StringBuilder b = new StringBuilder();
        b.append("CASE P=").append(p).append(" n=").append(n).append(" rate=").append(rate)
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

    public static void main(String[] args) {
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, "t23_probe2", "t23_probe2", "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode("t23_probe2", 4);
        System.out.println("ambient = " + MoneyHelper.getMathContext());
        one("135623", 6, "7.0");
        one("1014632", 6, "7.0");
        one("2345024", 6, "7.0");
        one("167299", 6, "21.6");
        one("64352", 12, "21.6");
        one("1000", 18, "18.5");
        one("246489", 18, "18.5");
        one("16838", 36, "16.8");
        one("40595", 36, "16.8");
        one("127704", 36, "16.8");
    }
}
