/*
 * Golden-vector capture harness — gerege-nbfi Fineract→Go migration, Tier 0.
 *
 * Runs the PINNED reference oracle (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a, JVM Zulu 21.0.11)
 * and prints OBSERVED schedules as JSON. It asserts nothing and predicts nothing — every value
 * printed is what the oracle emitted. No expected value is ever synthesised here.
 */
import org.apache.fineract.organisation.monetary.data.CurrencyData;
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

public class Capture {

    /** One capture run: a labelled input set. */
    record Case(String id, String purpose, LocalDate startDate, LocalDate disbursementDate, BigDecimal principal,
            int noRepayments, BigDecimal annualRate, int precision, RoundingMode mode, String currencyCode,
            int currencyDigits, DaysInMonthType dim, DaysInYearType diy, DaysInYearCustomStrategyType diyCustom,
            BigDecimal downPaymentPct, Integer installmentMultiplesOf, Integer fixedLength,
            boolean interestRecognitionOnDisbursementDate, boolean allowPartialPeriodInterestCalculation,
            boolean allowFullTermForTranche) {
    }

    static final LocalDate D_2024_01_01 = LocalDate.of(2024, 1, 1);

    static Case base(String id, String purpose, BigDecimal principal, int noRepayments, BigDecimal rate, int precision) {
        return new Case(id, purpose, D_2024_01_01, D_2024_01_01, principal, noRepayments, rate, precision,
                RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, false);
    }

    public static void main(String[] args) {
        final List<Case> cases = new ArrayList<>();

        // C-00 — CALIBRATION. Exactly the inputs of misc/Main.java and the shipped conformance test.
        // Must reproduce the already-transcribed literals or the whole run is void.
        cases.add(base("C-00", "calibration: reproduce shipped/README expectation", BigDecimal.valueOf(100), 6,
                BigDecimal.valueOf(7.0), 12));

        // D-01 — DISCRIMINATING VECTOR for the precision-vs-scale ambiguity (T5 §1).
        // 18 monthly installments, 18.5% p.a., principal 87,654,321, precision 12, HALF_UP.
        cases.add(base("D-01", "discriminates MathContext precision-vs-scale (T5 s1)",
                new BigDecimal("87654321"), 18, new BigDecimal("18.5"), 12));

        // D-01 precision sweep — the two precisions DEC-1 names, plus one lower.
        cases.add(base("D-01-p19", "same as D-01 at precision 19", new BigDecimal("87654321"), 18,
                new BigDecimal("18.5"), 19));
        cases.add(base("D-01-p8", "same as D-01 at precision 8", new BigDecimal("87654321"), 18,
                new BigDecimal("18.5"), 8));

        // D-01-mnt — identical arithmetic under an MNT-coded 2-minor-unit currency, to observe whether
        // the currency CODE (as opposed to its decimal places) participates in the arithmetic at all.
        Case d01 = cases.get(1);
        cases.add(new Case("D-01-mnt", "D-01 under MNT (2 minor units) — currency-code invariance probe",
                d01.startDate(), d01.disbursementDate(), d01.principal(), d01.noRepayments(), d01.annualRate(),
                d01.precision(), d01.mode(), "MNT", 2, d01.dim(), d01.diy(), d01.diyCustom(), d01.downPaymentPct(),
                d01.installmentMultiplesOf(), d01.fixedLength(), d01.interestRecognitionOnDisbursementDate(),
                d01.allowPartialPeriodInterestCalculation(), d01.allowFullTermForTranche()));

        // D-02 — MONTH-END ANCHORING (T5 §2). Disbursement on 31 January: does the oracle re-anchor to
        // the seed day-of-month after a clamp, or carry the clamped day forward?
        cases.add(new Case("D-02", "month-end re-anchor vs clamp-and-carry (T5 s2)", LocalDate.of(2024, 1, 31),
                LocalDate.of(2024, 1, 31), BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12,
                RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, false));

        // D-02b — 30 January seed: distinguishes "re-anchor to seed" from "carry the clamped day"
        // one step more sharply (Feb clamps to 29; March is 30 under re-anchor, 29 under carry).
        cases.add(new Case("D-02b", "month-end: 30 Jan seed, sharper discriminator", LocalDate.of(2024, 1, 30),
                LocalDate.of(2024, 1, 30), BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12,
                RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, false));

        // D-03 — ORDERING BOUNDARY (T5 §3): disbursement lands exactly on a repayment due date.
        // scheduleGenerationStartDate 2024-01-01 makes 2024-02-01 a due date; disburse on it.
        cases.add(new Case("D-03", "disbursement exactly on a repayment due date (ordering boundary, T5 s3)",
                D_2024_01_01, LocalDate.of(2024, 2, 1), BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12,
                RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, false));

        // D-04 — allowFullTermForTranche = true on a single-disbursement loan. T3b and T5 independently
        // refuted the "dead field" claim; this observes whether it changes the emitted schedule here.
        cases.add(new Case("D-04", "allowFullTermForTranche=true, single disbursement (T3b+T5 refutation)",
                D_2024_01_01, D_2024_01_01, BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12,
                RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, true));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"captures\": [\n");
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
        final MathContext mc = new MathContext(c.precision(), c.mode());
        final EmbeddableProgressiveLoanScheduleGenerator generator = new EmbeddableProgressiveLoanScheduleGenerator();
        final CurrencyData currency = new CurrencyData(c.currencyCode(), c.currencyCode(), c.currencyDigits(), null,
                c.currencyCode(), c.currencyCode());

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
        b.append("        \"currencyCode\": \"").append(c.currencyCode()).append("\",\n");
        b.append("        \"currencyDecimalPlaces\": ").append(c.currencyDigits()).append(",\n");
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
