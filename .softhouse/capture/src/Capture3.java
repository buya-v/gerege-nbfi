/*
 * Golden-vector capture harness, PASS 3 — gerege-nbfi Fineract→Go migration, Tier 0.
 *
 * Runs the PINNED reference oracle (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a) and prints
 * OBSERVED schedules as JSON. It asserts nothing and predicts nothing — every value printed is
 * what the oracle emitted. No expected value is ever synthesised here.
 *
 * WHY PASS 3 EXISTS: PRODUCTION SETTINGS.
 *
 * Buyan ratified the tenant parameters on 2026-08-18 (.softhouse/gates-proposed-answers.md):
 * rounding mode HALF_UP, licence NBFI. Precision is not a choice — MoneyHelper.PRECISION = 19 is a
 * compile-time constant and getMathContext() returns new MathContext(19, tenantRoundingMode)
 * [MoneyHelper.java:35, 91-93]. So the PRODUCTION MathContext is (19, HALF_UP).
 *
 * Passes 1 and 2 ran almost entirely at precision 12 or 8 — precisions production never runs. Those
 * captures proved the ambiguity moves money, which is exactly what they were for, but they are
 * DISCRIMINATION PROBES, not parity vectors. This pass re-captures at (19, HALF_UP) so a parity
 * corpus exists at the settings the Go module will actually have to match.
 *
 * TWO DISTINCT ROLES, DELIBERATELY BOTH PRESENT — do not conflate them:
 *
 *   P-CAL  is the RIG CALIBRATION. It runs at (12, HALF_UP) because that is what the shipped test
 *          expectation was produced at. It must reproduce that literal digit for digit, or this
 *          whole pass is void. It is NOT a parity vector.
 *   P-*    everything else runs at (19, HALF_UP) and is a PARITY candidate. A P-* figure is NOT
 *          expected to equal its pass-1/pass-2 counterpart; where it differs, the difference IS the
 *          finding, because it is the cost of the precision the corpus was never captured at.
 *
 * Every case sets the tenant rounding mode to HALF_UP(4) so the ambient MoneyHelper context is
 * (19, HALF_UP) too — matching production on both the parameter and the ambient path.
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

public class Capture3 {

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

    /** Production settings: tenant rounding HALF_UP(4), so the ambient context is (19, HALF_UP). */
    static Case prod(String id, String purpose, BigDecimal principal, int noRepayments, BigDecimal rate,
            int precision, Integer installmentMultiplesOf, boolean allowFullTermForTranche, String currencyCode,
            String tenantId) {
        return tenantCase(id, purpose, principal, noRepayments, rate, precision, installmentMultiplesOf,
                allowFullTermForTranche, currencyCode, tenantId, 4);
    }

    public static void main(String[] args) {
        final List<Case> cases = new ArrayList<>();

        // ---- RIG CALIBRATION — runs at the SHIPPED test's precision, not production's -----------
        // Must reproduce the shipped literal (EMI 17.01; splits 16.43/0.58, 16.52/0.49, 16.62/0.39,
        // 16.72/0.29, 16.81/0.20, 16.90/0.10; term 182; total interest 2.05) digit for digit.
        // If it does not, this pass is void and nothing below may be entered into the vector store.
        cases.add(prod("P-CAL", "RIG CALIBRATION at (12, HALF_UP) — must reproduce the shipped literal; NOT a parity vector",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, false, "usd", "cap_p_cal"));

        // ---- PARITY CANDIDATES at production (19, HALF_UP) -------------------------------------
        // P-00 — the calibration configuration re-run at production precision. The delta against
        // P-CAL is the direct price of the precision the corpus was never captured at.
        cases.add(prod("P-00", "C-00 configuration at PRODUCTION (19, HALF_UP)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19, null, false, "usd", "cap_p_00"));

        // P-01 — T5's discriminating configuration at production precision. D-01-p19 is its pass-1
        // counterpart and should agree; agreement across two harnesses is worth having.
        cases.add(prod("P-01", "18 x 18.5% principal 87,654,321 at PRODUCTION (19, HALF_UP)",
                new BigDecimal("87654321"), 18, new BigDecimal("18.5"), 19, null, false, "usd", "cap_p_01"));

        // P-02 / P-02b — month-end re-anchoring at production precision.
        cases.add(new Case("P-02", "month-end 31 Jan seed at PRODUCTION (19, HALF_UP)", LocalDate.of(2024, 1, 31),
                LocalDate.of(2024, 1, 31), BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19,
                RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, false, "cap_p_02", 4));
        cases.add(new Case("P-02b", "month-end 30 Jan seed at PRODUCTION (19, HALF_UP)", LocalDate.of(2024, 1, 30),
                LocalDate.of(2024, 1, 30), BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19,
                RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, false, "cap_p_02b", 4));

        // P-03 — ordering boundary at production precision. Buyan chose option (a): reproduce the
        // oracle's emitted order. This is the vector that pins it.
        cases.add(new Case("P-03", "disbursement exactly on a repayment due date at PRODUCTION (19, HALF_UP)",
                D_2024_01_01, LocalDate.of(2024, 2, 1), BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19,
                RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, false, "cap_p_03", 4));

        // P-04f / P-04t — G-1 item 5 as answered: pin false as an obligation AND spend one cheap
        // capture at true so the behaviour is documented rather than assumed dormant.
        cases.add(prod("P-04f", "allowFullTermForTranche=FALSE at PRODUCTION (19, HALF_UP)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19, null, false, "usd", "cap_p_04f"));
        cases.add(prod("P-04t", "allowFullTermForTranche=TRUE at PRODUCTION (19, HALF_UP)",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19, null, true, "usd", "cap_p_04t"));

        // ---- MNT-denominated parity candidates at production settings --------------------------
        // The corpus tops out at principal 245,000; ordinary Mongolian loans are ~20x that. Captured,
        // never extrapolated. MNT is ISO 4217 numeric 496, minor unit 2.
        cases.add(prod("P-MNT-5M", "MNT 5,000,000 / 18 x 18.5% at PRODUCTION (19, HALF_UP)",
                new BigDecimal("5000000"), 18, new BigDecimal("18.5"), 19, null, false, "MNT", "cap_p_mnt5m"));
        cases.add(prod("P-MNT-1M2", "MNT 1,200,000 / 12 x 21.6% at PRODUCTION (19, HALF_UP)",
                new BigDecimal("1200000"), 12, new BigDecimal("21.6"), 19, null, false, "MNT", "cap_p_mnt1m2"));
        cases.add(prod("P-MNT-50M", "MNT 50,000,000 / 36 x 16.8% at PRODUCTION (19, HALF_UP)",
                new BigDecimal("50000000"), 36, new BigDecimal("16.8"), 19, null, false, "MNT", "cap_p_mnt50m"));

        // ---- The RTGS threshold boundary (CLAUDE.md: MNT 5,000,000, from config) ----------------
        // Not a payment-rail test — a principal-size probe either side of a figure this program
        // treats as significant, so a later rail decision has schedule vectors on both sides.
        cases.add(prod("P-MNT-4M999", "MNT 4,999,999 / 18 x 18.5% at PRODUCTION (19, HALF_UP)",
                new BigDecimal("4999999"), 18, new BigDecimal("18.5"), 19, null, false, "MNT", "cap_p_mnt4m999"));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"pass\": 3,\n");
        sb.append("  \"harness\": \"Capture3.java\",\n");
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
