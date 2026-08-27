/*
 * T83 ORDER-DEPENDENCE PROBE — gerege-nbfi Fineract→Go migration, Tier 0. Gate G-8.
 *
 * WHY IT EXISTS. The driver's mid-flight note (`.softhouse/reviews/driver-rederivation-20260820-200002-G8.md`)
 * asks a question the boundary sweep cannot answer: is the reference oracle's non-zero final
 * balance a STALE MEMO, or is it a genuine statement that the loan is not amortized?
 *
 *   memo staleness      predicts the emitted balance is ORDER-DEPENDENT — a read taken after the
 *                       final-period EMI adjustment, with the memo forced to recompute, differs
 *                       from the value the schedule was emitted with.
 *   genuine non-amort   predicts NO order dependence: recomputing the same memo from the same
 *                       declared state yields the same number.
 *
 * THE EXPERIMENT, and it uses only the oracle's own public API.
 *
 *   1. Generate the schedule with the oracle's OWN ProgressiveLoanScheduleGenerator around the
 *      oracle's OWN ProgressiveEMICalculator behind a java.lang.reflect.Proxy that delegates every
 *      call unchanged and only remembers the ProgressiveLoanInterestScheduleModel reference. The
 *      plan is emitted alongside the pristine seam's plan and the two are compared cell for cell
 *      (PATH IDENTITY), so what follows is about the seam's computation and not a lookalike.
 *   2. Read the last repayment period's getOutstandingLoanBalance(). This is A — the value the
 *      emitted schedule carries.
 *   3. FORCE THE MEMO TO RECOMPUTE without changing the period's semantics. `Memo.get()` recomputes
 *      when a DECLARED dependency's hashCode moves (Memo.java, checkDependencyChangedAndUpdate) and
 *      the balance memo declares {paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount}
 *      (RepaymentPeriod.java:400). So: addPaidPrincipalAmount(+emi), then addPaidPrincipalAmount(-emi).
 *      paidPrincipal ends at the SAME VALUE it started at — the probe prints it before and after so
 *      a reader can check — but the memo has been invalidated and re-evaluated.
 *   4. Read getOutstandingLoanBalance() again. This is B.
 *
 * A != B means the emitted number depended on WHEN the memo was first populated relative to
 * `repaymentPeriod.setEmi(adjustedEmi)` (ProgressiveEMICalculator.java:1210). A == B refutes the
 * staleness account, and that refutation is the more valuable outcome.
 *
 * THE CONTROL IS LOAD-BEARING. The same procedure runs on CLEAN shapes — ones whose balance column
 * does reach zero. If the perturb-and-restore changed the answer THERE too, the probe would be
 * measuring its own perturbation rather than a stale memo, and nothing it says about the failing
 * shapes could be believed.
 *
 * THIS PROBE MUTATES NOTHING THAT IS EMITTED. The mutation happens strictly AFTER generate() has
 * returned its plan, on a throwaway in-JVM model, in a container that is destroyed at the end of the
 * run. It is NOT the capture: the capture is capture-t83-raw.json, taken through the pristine seam
 * by CaptureT83.java, and nothing here feeds it.
 *
 * PRODUCTION SETTINGS: (19, HALF_UP), tenant rounding ordinal 4, MNT at 2 decimal places, single
 * disbursement on the schedule start date, MONTHS/1, DECLINING_BALANCE, DAYS_30/DAYS_360, no down
 * payment, both multiples-of inputs null — every shape strictly inside DEC-1's graded domain.
 *
 * PostgreSQL remains the only permitted database for this program; this probe opens no database
 * connection and starts no server. "The oracle" is the Fineract reference implementation, never
 * Oracle Database (a prohibited product).
 */
import org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant;
import org.apache.fineract.infrastructure.core.service.ThreadLocalContextUtil;
import org.apache.fineract.organisation.monetary.data.CurrencyData;
import org.apache.fineract.organisation.monetary.domain.Money;
import org.apache.fineract.organisation.monetary.domain.MoneyHelper;
import org.apache.fineract.portfolio.common.domain.DaysInMonthType;
import org.apache.fineract.portfolio.common.domain.DaysInYearType;
import org.apache.fineract.portfolio.loanaccount.domain.Loan;
import org.apache.fineract.portfolio.loanaccount.domain.ProgressiveLoanModel;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlan;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDisbursementPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanDownPaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanRepaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.DefaultScheduledDateGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.ProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.ScheduledDateGenerator;
import org.apache.fineract.portfolio.loanaccount.service.InterestScheduleModelRepositoryWrapper;
import org.apache.fineract.portfolio.loanproduct.calc.EMICalculator;
import org.apache.fineract.portfolio.loanproduct.calc.ProgressiveEMICalculator;
import org.apache.fineract.portfolio.loanproduct.calc.data.ProgressiveLoanInterestScheduleModel;
import org.apache.fineract.portfolio.loanproduct.calc.data.RepaymentPeriod;
import org.apache.fineract.portfolio.loanproduct.domain.ILoanConfigurationDetails;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

public class ProbeOrderDep2 {

    record Shape(String id, String purpose, int principalMinor, int noRepayments, String rate, String tenantId) {
    }

    static final LocalDate D = LocalDate.of(2024, 1, 1);

    static String pl(BigDecimal d) {
        return d == null ? "null" : d.toPlainString();
    }

    public static void main(String[] args) throws Exception {
        final List<Shape> shapes = new ArrayList<>();
        // FAILING shapes — measured in capture-t83-raw.json as not reaching zero
        shapes.add(new Shape("OD2-FAM2-R600p0-N108-B1", "T84 FAMILY 2: MNT 0.01 / 108 x 600.0% -- oracle AND port both non-amortizing", 1, 108, "600.0", "od2_f2_a"));
        shapes.add(new Shape("OD2-FAM2-R600p0-N120-B1", "T84 FAMILY 2: MNT 0.01 / 120 x 600.0%", 1, 120, "600.0", "od2_f2_b"));
        shapes.add(new Shape("OD2-FAM2-R600p0-N104-B1", "T84 FAMILY 2: MNT 0.01 / 104 x 600.0%, the smallest n in family 2", 1, 104, "600.0", "od2_f2_c"));
        shapes.add(new Shape("OD2-FAM1-R3p6-N360-B109", "T84 FAMILY 1 at an ordinary 30-year term: MNT 1.09 / 360 x 3.6%", 109, 360, "3.6", "od2_f1_a"));
        shapes.add(new Shape("OD2-CLEAN-R600p0-N103-B1", "CONTROL: MNT 0.01 / 103 x 600.0%, one repayment short of family 2", 1, 103, "600.0", "od2_c_a"));
        shapes.add(new Shape("OD2-CLEAN-R3p6-N360-B110", "CONTROL: MNT 1.10 / 360 x 3.6%, the smallest clean principal there", 110, 360, "3.6", "od2_c_b"));
        shapes.add(new Shape("OD2-CLEAN-R21p6-N6-B120000000", "CONTROL: MNT 1,200,000 / 6 x 21.6% -- an ordinary loan", 120000000, 6, "21.6", "od2_c_c"));

        final StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"probe\": \"T83 order-dependence\",\n");
        sb.append("  \"question\": \"Is the reference oracle's non-zero final outstanding balance ORDER-DEPENDENT (a stale memo) or not (a genuine non-amortizing schedule)?\",\n");
        sb.append("  \"method\": \"After generate() returns, force the balance memo to recompute by moving a DECLARED dependency (paidPrincipal) and moving it back to the same value, then re-read. Memo.java recomputes on a declared dependency's hashCode change; RepaymentPeriod.java:400 declares {paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount} and NOT emi.\",\n");
        sb.append("  \"moneyHelperPrecision\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append("  \"cases\": [\n");
        final List<String> out = new ArrayList<>();
        for (Shape s : shapes) {
            out.add(run(s));
        }
        sb.append(String.join(",\n", out)).append("\n  ]\n}\n");
        System.out.println(sb);
    }

    static String run(final Shape s) {
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, s.tenantId(), s.tenantId(), "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(s.tenantId(), 4);
        final MathContext ambient = MoneyHelper.getMathContext();

        final MathContext mc = new MathContext(19, RoundingMode.HALF_UP);
        final CurrencyData currency = new CurrencyData("MNT", "MNT", 2, null, "MNT", "MNT");
        final BigDecimal principal = new BigDecimal(s.principalMinor()).movePointLeft(2);
        final LoanRepaymentScheduleModelData config = new LoanRepaymentScheduleModelData(D, currency, principal, D,
                s.noRepayments(), 1, "MONTHS", new BigDecimal(s.rate()), false, DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360, BigDecimal.ZERO, null, null, false, null,
                InterestMethod.DECLINING_BALANCE, true, false);

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(s.id()).append("\",\n");
        b.append("      \"purpose\": \"").append(s.purpose()).append("\",\n");
        b.append("      \"inputs\": {\"disbursementAmount\": \"").append(principal.toPlainString())
                .append("\", \"principalMinorUnits\": ").append(s.principalMinor())
                .append(", \"numberOfRepayments\": ").append(s.noRepayments())
                .append(", \"annualNominalInterestRate\": \"").append(s.rate())
                .append("\", \"currencyDecimalPlaces\": 2, \"mathContextPrecision\": 19, \"mathContextRoundingMode\": \"HALF_UP\", \"mathContextRoundingModeOrdinal\": 4")
                .append(", \"tenantId\": \"").append(s.tenantId()).append("\", \"ambientMoneyHelperMathContext\": \"")
                .append(ambient).append("\"},\n");

        // --- the pristine seam's plan: this is what a capture would emit -----------------------
        final LoanSchedulePlan seamPlan = new EmbeddableProgressiveLoanScheduleGenerator().generate(mc, config);

        // --- the instrumented run, which hands back the model ----------------------------------
        final ProgressiveLoanInterestScheduleModel[] captured = new ProgressiveLoanInterestScheduleModel[1];
        final ScheduledDateGenerator sdg = new DefaultScheduledDateGenerator();
        final EMICalculator realCalculator = new ProgressiveEMICalculator(sdg);
        final EMICalculator spy = (EMICalculator) Proxy.newProxyInstance(EMICalculator.class.getClassLoader(),
                new Class<?>[] { EMICalculator.class }, (proxy, method, args) -> {
                    final Object result;
                    try {
                        result = method.invoke(realCalculator, args);
                    } catch (InvocationTargetException ite) {
                        throw ite.getCause();
                    }
                    if ("generatePeriodInterestScheduleModel".equals(method.getName())
                            && result instanceof ProgressiveLoanInterestScheduleModel m) {
                        captured[0] = m;
                    }
                    return result;
                });
        final LoanSchedulePlan probePlan = new ProgressiveLoanScheduleGenerator(sdg, spy,
                new NoopModelRepositoryWrapper()).generate(mc, config);

        b.append("      \"pathIdentity\": {\"identical\": ")
                .append(renderPlan(seamPlan).equals(renderPlan(probePlan)))
                .append(", \"note\": \"the instrumented plan is compared cell for cell against the PRISTINE seam's plan; if this is false nothing below is about the seam's computation\"},\n");

        final LoanSchedulePlanPeriod lastEmitted = seamPlan.getPeriods().get(seamPlan.getPeriods().size() - 1);
        final String emittedBalance = lastEmitted instanceof LoanSchedulePlanRepaymentPeriod rp
                ? pl(rp.getOutstandingLoanBalance()) : "n/a";
        b.append("      \"emittedFinalRowBalance\": \"").append(emittedBalance).append("\",\n");

        if (captured[0] == null) {
            b.append("      \"modelCaptured\": false\n    }");
            ThreadLocalContextUtil.reset();
            return b.toString();
        }

        final List<RepaymentPeriod> periods = captured[0].repaymentPeriods();
        final RepaymentPeriod last = periods.get(periods.size() - 1);

        // A — the value the schedule was emitted with, read from the model the generator mutated.
        final Money a = last.getOutstandingLoanBalance();
        final String paidPrincipalBefore = pl(last.getPaidPrincipal().getAmount());
        final String emiAtRead = pl(last.getEmi().getAmount());
        final String duePrincipalAtRead = pl(last.getDuePrincipal().getAmount());

        // FORCE THE MEMO TO RECOMPUTE. Move a DECLARED dependency, then move it back to the same
        // value. Nothing about the period's semantics changes; only the memo's cached hash does.
        final Money bump = Money.of(currency, new BigDecimal("0.01"), mc);
        last.addPaidPrincipalAmount(bump);
        final Money intermediate = last.getOutstandingLoanBalance();
        last.addPaidPrincipalAmount(bump.negated(mc));
        final String paidPrincipalAfter = pl(last.getPaidPrincipal().getAmount());
        final Money bAfter = last.getOutstandingLoanBalance();

        b.append("      \"lastRepaymentPeriod\": {\n");
        b.append("        \"emiAtRead\": \"").append(emiAtRead).append("\",\n");
        b.append("        \"duePrincipalAtRead\": \"").append(duePrincipalAtRead).append("\",\n");
        b.append("        \"paidPrincipalBefore\": \"").append(paidPrincipalBefore).append("\",\n");
        b.append("        \"paidPrincipalAfter\": \"").append(paidPrincipalAfter).append("\",\n");
        b.append("        \"paidPrincipalRestored\": ").append(paidPrincipalBefore.equals(paidPrincipalAfter)).append(",\n");
        b.append("        \"A_balanceAsEmitted\": \"").append(pl(a.getAmount())).append("\",\n");
        b.append("        \"intermediate_balanceWhilePerturbed\": \"").append(pl(intermediate.getAmount())).append("\",\n");
        b.append("        \"B_balanceAfterForcedRecompute\": \"").append(pl(bAfter.getAmount())).append("\",\n");
        b.append("        \"orderDependent\": ").append(a.getAmount().compareTo(bAfter.getAmount()) != 0).append("\n");
        b.append("      }\n    }");
        ThreadLocalContextUtil.reset();
        return b.toString();
    }

    /** One canonical string for a whole plan, used only for the path-identity comparison. */
    static String renderPlan(final LoanSchedulePlan plan) {
        final StringBuilder s = new StringBuilder();
        s.append(plan.getLoanTermInDays()).append('|').append(pl(plan.getTotalDisbursedAmount())).append('|')
                .append(pl(plan.getTotalPrincipalAmount())).append('|').append(pl(plan.getTotalInterestAmount()))
                .append('|').append(pl(plan.getTotalFeeAmount())).append('|').append(pl(plan.getTotalPenaltyAmount()))
                .append('|').append(pl(plan.getTotalRepaymentAmount())).append('|')
                .append(pl(plan.getTotalOutstandingAmount()));
        for (LoanSchedulePlanPeriod p : plan.getPeriods()) {
            if (p instanceof LoanSchedulePlanDisbursementPeriod dp) {
                s.append("//D:").append(dp.periodFromDate()).append(':').append(dp.periodDueDate()).append(':')
                        .append(pl(dp.getPrincipalAmount())).append(':').append(pl(dp.getOutstandingLoanBalance()));
            } else if (p instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                s.append("//P:").append(dpp.periodNumber()).append(':').append(dpp.periodFromDate()).append(':')
                        .append(dpp.periodDueDate()).append(':').append(pl(dpp.getPrincipalAmount())).append(':')
                        .append(pl(dpp.getOutstandingLoanBalance()));
            } else if (p instanceof LoanSchedulePlanRepaymentPeriod rp) {
                s.append("//R:").append(rp.periodNumber()).append(':').append(rp.periodFromDate()).append(':')
                        .append(rp.periodDueDate()).append(':').append(pl(rp.getPrincipalAmount())).append(':')
                        .append(pl(rp.getInterestAmount())).append(':').append(pl(rp.getTotalDueAmount())).append(':')
                        .append(pl(rp.getOutstandingLoanBalance()));
            } else {
                s.append("//?:").append(p.getClass().getName());
            }
        }
        return s.toString();
    }

    /**
     * Byte-for-byte the NoopInterestScheduleModelRepositoryWrapper the pinned seam class declares
     * privately (EmbeddableProgressiveLoanScheduleGenerator.java), reproduced here only because a
     * private nested class cannot be referenced from outside its own file. The seam class itself is
     * NOT modified.
     */
    private static final class NoopModelRepositoryWrapper implements InterestScheduleModelRepositoryWrapper {

        @Override
        public Optional<ProgressiveLoanModel> findOneByLoanId(Long loanId) {
            return Optional.empty();
        }

        @Override
        public Optional<ProgressiveLoanModel> findOneByLoan(Loan loan) {
            return Optional.empty();
        }

        @Override
        public Optional<ProgressiveLoanInterestScheduleModel> extractModel(Optional<ProgressiveLoanModel> progressiveLoanModel) {
            return Optional.empty();
        }

        @Override
        public ProgressiveLoanInterestScheduleModel writeInterestScheduleModel(Loan loan, ProgressiveLoanInterestScheduleModel model) {
            return null;
        }

        @Override
        public Optional<ProgressiveLoanInterestScheduleModel> readProgressiveLoanInterestScheduleModel(Long loanId,
                ILoanConfigurationDetails detail, Integer installmentAmountInMultipliesOf) {
            return Optional.empty();
        }

        @Override
        public boolean hasValidModelForDate(Long loanId, LocalDate targetDate) {
            return false;
        }

        @Override
        public Optional<ProgressiveLoanInterestScheduleModel> getSavedModel(Loan loan, LocalDate businessDate) {
            return Optional.empty();
        }

        @Override
        public Long removeByLoanId(Long loanId) {
            return 0L;
        }
    }
}
