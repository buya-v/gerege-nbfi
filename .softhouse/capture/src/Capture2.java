/*
 * Golden-vector capture harness, PASS 2 — gerege-nbfi Fineract→Go migration, Tier 0.
 *
 * Runs the PINNED reference oracle (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a) and prints
 * OBSERVED schedules as JSON. It asserts nothing and predicts nothing — every value printed is
 * what the oracle emitted. No expected value is ever synthesised here.
 *
 * WHAT PASS 2 ADDS OVER Capture.java: a TENANT CONTEXT.
 *
 * Pass 1's D-04 died with "No tenant context available. MoneyHelper requires a valid tenant
 * context" (MoneyHelper.java:178-179). Two whole classes of behaviour are unreachable without a
 * tenant, and both are open questions on gate G-1:
 *
 *   (a) allowFullTermForTranche = true  — the branch that reaches MoneyHelper at all.
 *   (b) installmentAmountInMultiplesOf != null — Money.java:154 calls MoneyHelper.getRoundingMode().
 *       T17 called this "the single largest gap" and "the highest-risk one for the Mongolian market";
 *       it is null at all 97 in-seam occurrences, so no test pins it.
 *
 * A tenant also makes the AMBIENT MathContext observable: MoneyHelper.PRECISION = 19 (MoneyHelper.java:35)
 * combined with the tenant's configured rounding mode, which is a DIFFERENT MathContext from the one
 * threaded as a parameter. G-1 decision 6 asks what the Mongolian tenant's rounding mode should be;
 * the pairs below observe whether that choice moves a payable amount.
 *
 * Rounding-mode values are the ints MoneyHelper.initializeTenantRoundingMode takes and validates
 * 0..6 (MoneyHelper.java:182-189), converted with RoundingMode.valueOf(int). 4 = HALF_UP, 6 = HALF_EVEN
 * (application.properties:77 defaults the tenant to 6; the unit tests mock HALF_UP).
 *
 * Each case uses its OWN tenant identifier so no cache entry is shared between cases
 * (roundingModeCache / mathContextCache are static and keyed by tenant id, MoneyHelper.java:37-38).
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

public class Capture2 {

    /**
     * One capture run. Same shape as pass 1's Case plus the tenant fields.
     * tenantRoundingMode is the int handed to MoneyHelper.initializeTenantRoundingMode, or null to
     * run with NO tenant context at all (reproducing pass 1's environment as a control).
     */
    record Case(String id, String purpose, LocalDate startDate, LocalDate disbursementDate, BigDecimal principal,
            int noRepayments, BigDecimal annualRate, int precision, RoundingMode mode, String currencyCode,
            int currencyDigits, DaysInMonthType dim, DaysInYearType diy, DaysInYearCustomStrategyType diyCustom,
            BigDecimal downPaymentPct, Integer installmentMultiplesOf, Integer fixedLength,
            boolean interestRecognitionOnDisbursementDate, boolean allowPartialPeriodInterestCalculation,
            boolean allowFullTermForTranche, String tenantId, Integer tenantRoundingMode) {
    }

    static final LocalDate D_2024_01_01 = LocalDate.of(2024, 1, 1);

    /** C-00's inputs exactly, varied only by the fields a caller overrides. */
    static Case tenantCase(String id, String purpose, BigDecimal principal, int noRepayments, BigDecimal rate,
            int precision, Integer installmentMultiplesOf, boolean allowFullTermForTranche, String currencyCode,
            String tenantId, Integer tenantRoundingMode) {
        return new Case(id, purpose, D_2024_01_01, D_2024_01_01, principal, noRepayments, rate, precision,
                RoundingMode.HALF_UP, currencyCode, 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, installmentMultiplesOf, null, false, true, allowFullTermForTranche, tenantId,
                tenantRoundingMode);
    }

    public static void main(String[] args) {
        final List<Case> cases = new ArrayList<>();

        // ---- Controls -------------------------------------------------------------------------
        // T-00-notenant — C-00's inputs with NO tenant context. Must reproduce pass 1's C-00 exactly.
        // If it does not, pass 2's environment differs from pass 1's and nothing below is comparable.
        cases.add(tenantCase("T-00-notenant", "control: C-00 inputs, NO tenant context (must equal pass-1 C-00)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, false, "usd", null, null));

        // T-00-he / T-00-hu — C-00's inputs WITH a tenant, under each candidate rounding mode.
        // On a path that never consults MoneyHelper these must both still equal C-00. Any difference
        // means the ambient context reaches the base schedule path, which would be a finding in itself.
        cases.add(tenantCase("T-00-he", "control: C-00 inputs, tenant rounding HALF_EVEN(6)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, false, "usd", "cap_t00_he", 6));
        cases.add(tenantCase("T-00-hu", "control: C-00 inputs, tenant rounding HALF_UP(4)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, false, "usd", "cap_t00_hu", 4));

        // ---- (a) allowFullTermForTranche — closes pass 1's D-04 error --------------------------
        // T-04f is the differential control: identical inputs, flag false.
        cases.add(tenantCase("T-04f", "allowFullTermForTranche=FALSE, single disbursement, tenant HALF_EVEN(6)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, false, "usd", "cap_t04f", 6));
        cases.add(tenantCase("T-04t", "allowFullTermForTranche=TRUE, single disbursement, tenant HALF_EVEN(6) [pass-1 D-04 retry]",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, true, "usd", "cap_t04t", 6));
        // Same pair at the large principal, where a one-minor-unit difference is easier to see.
        cases.add(tenantCase("T-04f-big", "allowFullTermForTranche=FALSE, 18x18.5% principal 87654321, tenant HALF_EVEN(6)",
                new BigDecimal("87654321"), 18, new BigDecimal("18.5"), 12, null, false, "usd", "cap_t04fb", 6));
        cases.add(tenantCase("T-04t-big", "allowFullTermForTranche=TRUE, 18x18.5% principal 87654321, tenant HALF_EVEN(6)",
                new BigDecimal("87654321"), 18, new BigDecimal("18.5"), 12, null, true, "usd", "cap_t04tb", 6));

        // ---- (b) installmentAmountInMultiplesOf — T17's "single largest gap" -------------------
        // null at all 97 in-seam occurrences, so no test pins it. The path engages
        // MoneyHelper.getRoundingMode() at Money.java:154, hence it needs the tenant.
        // HALF_EVEN vs HALF_UP on the SAME inputs isolates the ambient rounding mode's effect.
        cases.add(tenantCase("T-IM100-he", "installmentAmountInMultiplesOf=100, tenant HALF_EVEN(6)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, 100, false, "usd", "cap_im100_he", 6));
        cases.add(tenantCase("T-IM100-hu", "installmentAmountInMultiplesOf=100, tenant HALF_UP(4)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, 100, false, "usd", "cap_im100_hu", 4));
        cases.add(tenantCase("T-IM1-he", "installmentAmountInMultiplesOf=1, tenant HALF_EVEN(6)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, 1, false, "usd", "cap_im1_he", 6));

        // ---- MNT scale — the other total gap (T17 gap 3) ---------------------------------------
        // Largest principal carrying a literal schedule anywhere in the seam is 245,000. A routine
        // MNT 5,000,000 loan is ~20x that. Captured, never extrapolated.
        cases.add(tenantCase("T-MNT5M-he", "MNT 5,000,000 / 18 x 18.5% / multiplesOf=100, tenant HALF_EVEN(6)",
                new BigDecimal("5000000"), 18, new BigDecimal("18.5"), 12, 100, false, "MNT", "cap_mnt5m_he", 6));
        cases.add(tenantCase("T-MNT5M-hu", "MNT 5,000,000 / 18 x 18.5% / multiplesOf=100, tenant HALF_UP(4)",
                new BigDecimal("5000000"), 18, new BigDecimal("18.5"), 12, 100, false, "MNT", "cap_mnt5m_hu", 4));
        cases.add(tenantCase("T-MNT5M-plain-he", "MNT 5,000,000 / 18 x 18.5% / multiplesOf=null, tenant HALF_EVEN(6)",
                new BigDecimal("5000000"), 18, new BigDecimal("18.5"), 12, null, false, "MNT", "cap_mnt5mp_he", 6));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"pass\": 2,\n");
        sb.append("  \"harness\": \"Capture2.java\",\n");
        sb.append("  \"moneyHelperPrecision\": ").append(MoneyHelper.PRECISION).append(",\n");
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
        // Establish (or deliberately withhold) the tenant context for THIS case only.
        String ambientMathContext;
        if (c.tenantId() == null) {
            ThreadLocalContextUtil.reset();
            ambientMathContext = "null (no tenant context)";
        } else {
            ThreadLocalContextUtil.setTenant(
                    new FineractPlatformTenant(1L, c.tenantId(), c.tenantId(), "Asia/Ulaanbaatar", null));
            MoneyHelper.initializeTenantRoundingMode(c.tenantId(), c.tenantRoundingMode());
            try {
                ambientMathContext = String.valueOf(MoneyHelper.getMathContext());
            } catch (RuntimeException e) {
                ambientMathContext = e.getClass().getName() + ": " + e.getMessage();
            }
        }

        final MathContext mc = new MathContext(c.precision(), c.mode());
        final EmbeddableProgressiveLoanScheduleGenerator generator = new EmbeddableProgressiveLoanScheduleGenerator();
        final CurrencyData currency = new CurrencyData(c.currencyCode(), c.currencyCode(), c.currencyDigits(),
                c.installmentMultiplesOf(), c.currencyCode(), c.currencyCode());

        final LoanRepaymentScheduleModelData config = new LoanRepaymentScheduleModelData(c.startDate(), currency,
                c.principal(), c.disbursementDate(), c.noRepayments(), 1, "MONTHS", c.annualRate(),
                BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0, c.dim(), c.diy(), c.downPaymentPct(),
                c.installmentMultiplesOf(), c.fixedLength(), c.interestRecognitionOnDisbursementDate(), c.diyCustom(),
                InterestMethod.DECLINING_BALANCE, c.allowPartialPeriodInterestCalculation(),
                c.allowFullTermForTranche());

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"purpose\": \"").append(c.purpose()).append("\",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"scheduleGenerationStartDate\": \"").append(c.startDate()).append("\",\n");
        b.append("        \"disbursementDate\": \"").append(c.disbursementDate()).append("\",\n");
        b.append("        \"disbursementAmount\": \"").append(c.principal()).append("\",\n");
        b.append("        \"numberOfRepayments\": ").append(c.noRepayments()).append(",\n");
        b.append("        \"repaymentFrequency\": 1,\n");
        b.append("        \"repaymentFrequencyType\": \"MONTHS\",\n");
        b.append("        \"annualNominalInterestRate\": \"").append(c.annualRate()).append("\",\n");
        b.append("        \"mathContextPrecision\": ").append(c.precision()).append(",\n");
        b.append("        \"mathContextRoundingMode\": \"").append(c.mode()).append("\",\n");
        b.append("        \"tenantId\": ").append(c.tenantId() == null ? "null" : "\"" + c.tenantId() + "\"").append(",\n");
        b.append("        \"tenantRoundingModeValue\": ").append(c.tenantRoundingMode()).append(",\n");
        b.append("        \"ambientMoneyHelperMathContext\": \"").append(ambientMathContext).append("\",\n");
        b.append("        \"currencyCode\": \"").append(c.currencyCode()).append("\",\n");
        b.append("        \"currencyDecimalPlaces\": ").append(c.currencyDigits()).append(",\n");
        b.append("        \"currencyInMultiplesOf\": ").append(c.installmentMultiplesOf()).append(",\n");
        b.append("        \"daysInMonth\": \"").append(c.dim()).append("\",\n");
        b.append("        \"daysInYear\": \"").append(c.diy()).append("\",\n");
        b.append("        \"daysInYearCustomStrategy\": ").append(c.diyCustom() == null ? "null" : "\"" + c.diyCustom() + "\"").append(",\n");
        b.append("        \"downPaymentEnabled\": ").append(BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0).append(",\n");
        b.append("        \"downPaymentPercentage\": \"").append(c.downPaymentPct()).append("\",\n");
        b.append("        \"installmentAmountInMultiplesOf\": ").append(c.installmentMultiplesOf()).append(",\n");
        b.append("        \"fixedLength\": ").append(c.fixedLength()).append(",\n");
        b.append("        \"interestRecognitionOnDisbursementDate\": ").append(c.interestRecognitionOnDisbursementDate()).append(",\n");
        b.append("        \"interestMethod\": \"DECLINING_BALANCE\",\n");
        b.append("        \"allowPartialPeriodInterestCalculation\": ").append(c.allowPartialPeriodInterestCalculation()).append(",\n");
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
        b.append("        \"totalDisbursedAmount\": \"").append(plan.getTotalDisbursedAmount()).append("\",\n");
        b.append("        \"totalInterestAmount\": \"").append(plan.getTotalInterestAmount()).append("\",\n");
        b.append("        \"totalRepaymentAmount\": \"").append(plan.getTotalRepaymentAmount()).append("\",\n");
        b.append("        \"periods\": [\n");

        final List<String> rows = new ArrayList<>();
        for (LoanSchedulePlanPeriod period : plan.getPeriods()) {
            if (period instanceof LoanSchedulePlanDisbursementPeriod dp) {
                rows.add("          {\"type\": \"DISBURSEMENT\", \"dueDate\": \"" + dp.periodDueDate()
                        + "\", \"principal\": \"" + dp.getPrincipalAmount() + "\"}");
            } else if (period instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                rows.add("          {\"type\": \"DOWN_PAYMENT\", \"periodNumber\": " + dpp.periodNumber()
                        + ", \"dueDate\": \"" + dpp.periodDueDate() + "\", \"balance\": \""
                        + dpp.getOutstandingLoanBalance() + "\", \"principal\": \"" + dpp.getPrincipalAmount()
                        + "\", \"total\": \"" + dpp.getTotalDueAmount() + "\", \"totalOutstandingBalance\": \""
                        + dpp.getTotalOutstandingLoanBalance() + "\"}");
            } else if (period instanceof LoanSchedulePlanRepaymentPeriod rp) {
                rows.add("          {\"type\": \"REPAYMENT\", \"periodNumber\": " + rp.periodNumber()
                        + ", \"dueDate\": \"" + rp.periodDueDate() + "\", \"balance\": \""
                        + rp.getOutstandingLoanBalance() + "\", \"principal\": \"" + rp.getPrincipalAmount()
                        + "\", \"interest\": \"" + rp.getInterestAmount() + "\", \"total\": \""
                        + rp.getTotalDueAmount() + "\", \"totalOutstandingBalance\": \""
                        + rp.getTotalOutstandingLoanBalance() + "\"}");
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
}
