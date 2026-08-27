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

/* T21-v2 AUDIT PROBE 2 — compact p12-vs-p19 divergence sweep against the pinned oracle.
 * Prints one line per (shape, principal): the two totals and whether the FULL schedules match. */
public class T21v2Probe2 {

    static final LocalDate D = LocalDate.of(2024, 1, 1);
    static int seq = 0;

    static String run(MathContext mc, BigDecimal principal, int n, BigDecimal rate) {
        String id = "t21v2b_" + (seq++);
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, id, id, "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(id, 4);
        CurrencyData c = new CurrencyData("MNT", "MNT", 2, null, "MNT", "MNT");
        LoanRepaymentScheduleModelData m = new LoanRepaymentScheduleModelData(D, c, principal, D, n, 1, "MONTHS", rate,
                false, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, BigDecimal.ZERO, null, null, false, null,
                InterestMethod.DECLINING_BALANCE, true, false);
        LoanSchedulePlan p = new EmbeddableProgressiveLoanScheduleGenerator().generate(mc, m);
        StringBuilder b = new StringBuilder();
        b.append(p.getTotalInterestAmount()).append("|").append(p.getTotalRepaymentAmount()).append("|");
        for (LoanSchedulePlanPeriod x : p.getPeriods()) {
            if (x instanceof LoanSchedulePlanRepaymentPeriod r) {
                b.append(r.periodNumber()).append(",").append(r.getPrincipalAmount()).append(",")
                        .append(r.getInterestAmount()).append(",").append(r.getOutstandingLoanBalance()).append(",")
                        .append(r.getTotalOutstandingLoanBalance()).append(";");
            }
        }
        return b.toString();
    }

    public static void main(String[] args) {
        MathContext p12 = new MathContext(12, RoundingMode.HALF_UP);
        MathContext p19 = new MathContext(19, RoundingMode.HALF_UP);
        Object[][] cases = { { 36, "16.8", "4" }, { 36, "16.8", "59" }, { 36, "16.8", "72" }, { 36, "16.8", "340" },
                { 36, "16.8", "426" }, { 36, "16.8", "6940" }, { 36, "16.8", "50000000" }, { 6, "7.0", "43811" },
                { 6, "7.0", "131432" }, { 6, "7.0", "131433" }, { 6, "7.0", "100" }, { 6, "7.0", "87654321" },
                { 18, "18.5", "5000000" }, { 18, "18.5", "4999999" }, { 18, "18.5", "87654321" },
                { 12, "21.6", "1200000" }, { 18, "18.5", "199999" } };
        for (Object[] cs : cases) {
            int n = (Integer) cs[0];
            BigDecimal rate = new BigDecimal((String) cs[1]);
            BigDecimal P = new BigDecimal((String) cs[2]);
            String a = run(p12, P, n, rate);
            String b = run(p19, P, n, rate);
            String[] ta = a.split("\\|");
            String[] tb = b.split("\\|");
            System.out.println(String.format("%3d x %-5s  principal %-10s  p12 int=%-12s rep=%-13s | p19 int=%-12s rep=%-13s | %s",
                    n, cs[1], cs[2], ta[0], ta[1], tb[0], tb[1], a.equals(b) ? "IDENTICAL" : "DIFFERENT"));
        }
    }
}
