/*
 * T50 TIER 2 -- the same separation, reached at the REAL CALL SITES.
 *
 * Tier 1 (CaptureT50Ambient.java) transcribed the expressions at
 *   ProgressiveLoanScheduleGenerator.java:445-446, :464-465   (N46-1)
 *   MathUtil.java:472-473 / LoanApplicationTerms.java:865-866 (N46-3)
 * and ran them against the oracle's own Money / MoneyHelper / MathUtil bytes.  A transcription
 * can still be wrong about its surroundings, so Tier 2 enters the oracle's OWN METHODS:
 *
 *   L1  ProgressiveLoanScheduleGenerator#calculateInstallmentCharge(PrincipalInterest, Money,
 *       LoanCharge, MathContext)                    -- private; reached by reflection.
 *   L2  ProgressiveLoanScheduleGenerator#calculateSpecificDueDateChargeWithPercentage(Money,
 *       Money, Money, LoanCharge, MathContext)      -- private; reached by reflection.
 *   L3  LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext) ->
 *       the Builder -> the constructor at :865-866; observation is getDownPaymentAmount().
 *       PUBLIC static factory -- no reflection, and it IS the site N46-3 names.
 *   L4  ProgressiveLoanScheduleGenerator#generate(mc, LoanApplicationTerms, Set<LoanCharge>,
 *       HolidayDetailDTO)  -- the :87 overload, the SERVER path, with a real percentage-based
 *       instalment-fee LoanCharge attached.  PUBLIC.
 *
 * LoanCharge is a JPA entity with no usable constructor, so it is allocated with
 * sun.misc.Unsafe#allocateInstance and its fields are set reflectively -- NO Fineract source is
 * modified or copied; the class bytes executed are the oracle's own, out of
 * BOOT-INF/lib/fineract-loan-*.jar.
 *
 * The generator is wired exactly as the shipped embeddable seam wires it
 * (EmbeddableProgressiveLoanScheduleGenerator.java:39-43): DefaultScheduledDateGenerator,
 * ProgressiveEMICalculator over it, and a no-op InterestScheduleModelRepositoryWrapper.
 *
 * IT ASSERTS NOTHING AND PREDICTS NOTHING.  Everything printed is what the oracle emitted.
 * Exact BigDecimal text only -- no float or double anywhere in this harness.
 */
import org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant;
import org.apache.fineract.infrastructure.core.service.ThreadLocalContextUtil;
import org.apache.fineract.organisation.monetary.data.CurrencyData;
import org.apache.fineract.organisation.monetary.domain.Money;
import org.apache.fineract.organisation.monetary.domain.MoneyHelper;
import org.apache.fineract.portfolio.common.domain.DaysInMonthType;
import org.apache.fineract.portfolio.common.domain.DaysInYearType;
import org.apache.fineract.portfolio.loanaccount.domain.Loan;
import org.apache.fineract.portfolio.loanaccount.domain.LoanCharge;
import org.apache.fineract.portfolio.loanaccount.domain.ProgressiveLoanModel;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.DefaultScheduledDateGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanApplicationTerms;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanScheduleModel;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanScheduleModelPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.PrincipalInterest;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.ProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.ScheduledDateGenerator;
import org.apache.fineract.portfolio.loanaccount.service.InterestScheduleModelRepositoryWrapper;
import org.apache.fineract.portfolio.loanproduct.calc.EMICalculator;
import org.apache.fineract.portfolio.loanproduct.calc.ProgressiveEMICalculator;
import org.apache.fineract.portfolio.loanproduct.calc.data.ProgressiveLoanInterestScheduleModel;
import org.apache.fineract.portfolio.loanproduct.domain.ILoanConfigurationDetails;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

public class CaptureT50Tier2 {

    static final Integer AMBIENT_ABSENT = null;
    static final int[] MODE_ORDINALS = { 0, 1, 2, 3, 4, 5, 6 };

    /** ChargeCalculationType [ChargeCalculationType.java:25-30]. */
    static final int CALC_PERCENT_OF_AMOUNT = 2;
    static final int CALC_PERCENT_OF_AMOUNT_AND_INTEREST = 3;
    static final int CALC_PERCENT_OF_INTEREST = 4;
    /** ChargeTimeType [ChargeTimeType.java:24-40]. */
    static final int TIME_SPECIFIED_DUE_DATE = 2;
    static final int TIME_INSTALMENT_FEE = 8;

    record Leg(String id, String source, String what) {
    }

    record Val(String name, String principal, String interest, String percentage, int calcType, String why) {
    }

    record Case(String id, Leg leg, Val val, Integer ambientOrdinal, int threadedOrdinal) {
    }

    static final Leg L1 = new Leg("L1-calculateInstallmentCharge",
            "ProgressiveLoanScheduleGenerator.java:432-452 (private, reached by reflection)",
            "the real N46-1 method; returns cumulative after adding the percentage charge");
    static final Leg L2 = new Leg("L2-calculateSpecificDueDateChargeWithPercentage",
            "ProgressiveLoanScheduleGenerator.java:454-468 (private, reached by reflection)",
            "the second real N46-1 method");
    static final Leg L3 = new Leg("L3-downPaymentAmount",
            "LoanApplicationTerms.java:865-866 via the public static assembleFrom(modelData, mc)",
            "the real N46-3 down-payment site; observation is getDownPaymentAmount()");
    static final Leg L4 = new Leg("L4-generate-87-with-instalment-fee",
            "ProgressiveLoanScheduleGenerator.java:87 generate(mc, terms, charges, detailDTO)",
            "the SERVER-path overload with a percentage instalment fee attached");

    static final Leg L5 = new Leg("L5-downPaymentAmount-ambient-ctor",
            "LoanApplicationTerms.java:863-869 via the public static long assembleFrom(...) at :609",
            "the SERVER-path down-payment site (the :747 constructor), reached by reflection over the "
                    + "76-parameter overload with everything but currency/principal/downPayment left at its type default");

    static final List<Leg> LEGS = List.of(L1, L2, L3, L4, L5);

    // ---- values ---------------------------------------------------------------------------
    // Chosen so the rounding step under test lands on an EXACT tie at MNT's 2 decimal places.
    static final List<Val> VALS = List.of(
            new Val("W1-tie-amt", "100.50", "0", "1", CALC_PERCENT_OF_AMOUNT,
                    "principal 100.50 x 1% = 1.005 exactly -- scale-2 tie, last kept digit 0 (even)"),
            new Val("W2-tie-amt-and-interest", "100.00", "0.50", "1", CALC_PERCENT_OF_AMOUNT_AND_INTEREST,
                    "(100.00 + 0.50) x 1% = 1.005 exactly -- exercises the principal+interest branch"),
            new Val("W3-tie-interest", "0", "100.50", "1", CALC_PERCENT_OF_INTEREST,
                    "interest 100.50 x 1% = 1.005 exactly -- exercises the interest-only branch"),
            new Val("W4-tie-mnt", "4020100.50", "0", "25", CALC_PERCENT_OF_AMOUNT,
                    "4,020,100.50 x 25% = 1,005,025.125 exactly -- MNT-sized scale-2 tie"),
            new Val("W5-noTie", "100.00", "0", "1", CALC_PERCENT_OF_AMOUNT,
                    "100.00 x 1% = 1.0000 exactly -- NULL CONTROL, no rounding decision exists"));

    // L3 reuses the same pairs, reading `percentage` as the down-payment percentage and
    // `principal` as the disbursement amount.

    static CurrencyData mnt() {
        return new CurrencyData("MNT", "Mongolian Togrog", 2, null, "MNT", "MNT");
    }

    static String esc(String s) {
        return s == null ? ""
                : s.replace("\\", "\\\\").replace("\"", "'").replace("\n", " | ").replace("\r", " ").replace("\t", " ");
    }

    // ---- LoanCharge, allocated without a constructor ----------------------------------------

    static Object unsafe;
    static Method allocateInstance;

    static void initUnsafe() throws Exception {
        Class<?> u = Class.forName("sun.misc.Unsafe");
        Field f = u.getDeclaredField("theUnsafe");
        f.setAccessible(true);
        unsafe = f.get(null);
        allocateInstance = u.getMethod("allocateInstance", Class.class);
    }

    static void set(Object target, String field, Object value) throws Exception {
        Class<?> c = target.getClass();
        while (c != null) {
            try {
                Field fd = c.getDeclaredField(field);
                fd.setAccessible(true);
                fd.set(target, value);
                return;
            } catch (NoSuchFieldException e) {
                c = c.getSuperclass();
            }
        }
        throw new NoSuchFieldException(field + " on " + target.getClass());
    }

    static LoanCharge newLoanCharge(int chargeTime, int calcType, String percentage, LocalDate dueDate) throws Exception {
        LoanCharge lc = (LoanCharge) allocateInstance.invoke(unsafe, LoanCharge.class);
        set(lc, "chargeTime", chargeTime);
        set(lc, "chargeCalculation", calcType);
        set(lc, "percentage", new BigDecimal(percentage));
        set(lc, "amountOrPercentage", new BigDecimal(percentage));
        set(lc, "amount", BigDecimal.ZERO);
        set(lc, "amountOutstanding", BigDecimal.ZERO);
        set(lc, "amountPaid", BigDecimal.ZERO);
        set(lc, "amountWaived", BigDecimal.ZERO);
        set(lc, "amountWrittenOff", BigDecimal.ZERO);
        set(lc, "taxAmount", BigDecimal.ZERO);
        set(lc, "penaltyCharge", Boolean.FALSE);
        set(lc, "paid", Boolean.FALSE);
        set(lc, "waived", Boolean.FALSE);
        set(lc, "active", Boolean.TRUE);
        set(lc, "dueDate", dueDate);
        set(lc, "submittedOnDate", dueDate);
        return lc;
    }

    // ---- the generator, wired exactly as the shipped embeddable seam wires it ----------------

    static ProgressiveLoanScheduleGenerator newGenerator() {
        final ScheduledDateGenerator sdg = new DefaultScheduledDateGenerator();
        final EMICalculator emi = new ProgressiveEMICalculator(sdg);
        return new ProgressiveLoanScheduleGenerator(sdg, emi, new NoopWrapper());
    }

    static final class NoopWrapper implements InterestScheduleModelRepositoryWrapper {

        @Override
        public Optional<ProgressiveLoanModel> findOneByLoanId(Long loanId) {
            return Optional.empty();
        }

        @Override
        public Optional<ProgressiveLoanModel> findOneByLoan(Loan loan) {
            return Optional.empty();
        }

        @Override
        public Optional<ProgressiveLoanInterestScheduleModel> extractModel(Optional<ProgressiveLoanModel> m) {
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

    // ---- cases -------------------------------------------------------------------------------

    static List<Case> cases() {
        final List<Case> out = new ArrayList<>();
        final List<Integer> ambients = new ArrayList<>();
        for (int o : MODE_ORDINALS) {
            ambients.add(o);
        }
        ambients.add(AMBIENT_ABSENT);
        for (Leg leg : LEGS) {
            for (Val v : VALS) {
                for (Integer amb : ambients) {
                    for (int thr : MODE_ORDINALS) {
                        out.add(new Case(leg.id() + "__" + v.name() + "__A" + (amb == null ? "ABSENT" : String.valueOf(amb)) + "__T"
                                + thr, leg, v, amb, thr));
                    }
                }
            }
        }
        return out;
    }

    static String ambientCanary() {
        final String tenantId = "t50t2_canary_never_initialised";
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenantId, tenantId, "Asia/Ulaanbaatar", null));
        try {
            return "NO THROW -- ambient read succeeded: " + MoneyHelper.getMathContext();
        } catch (RuntimeException e) {
            return "THREW " + e.getClass().getName() + ": " + esc(String.valueOf(e.getMessage()));
        }
    }

    static final LocalDate DISBURSE = LocalDate.of(2026, 1, 1);
    static final LocalDate START = LocalDate.of(2026, 2, 1);

    static String run(final Case c) throws Exception {
        final String tenantId = "t50t2_" + c.id().toLowerCase().replace('-', '_');
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenantId, tenantId, "Asia/Ulaanbaatar", null));
        if (c.ambientOrdinal() != null) {
            MoneyHelper.initializeTenantRoundingMode(tenantId, c.ambientOrdinal());
        }
        String ambientEcho;
        try {
            ambientEcho = String.valueOf(MoneyHelper.getMathContext());
        } catch (RuntimeException e) {
            ambientEcho = "THREW " + e.getClass().getName() + ": " + esc(String.valueOf(e.getMessage()));
        }

        final MathContext mc = new MathContext(19, RoundingMode.values()[c.threadedOrdinal()]);
        final CurrencyData currency = mnt();
        final Val v = c.val();

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"leg\": \"").append(c.leg().id()).append("\",\n");
        b.append("      \"legSource\": \"").append(esc(c.leg().source())).append("\",\n");
        b.append("      \"legWhat\": \"").append(esc(c.leg().what())).append("\",\n");
        b.append("      \"value\": \"").append(v.name()).append("\",\n");
        b.append("      \"valueWhy\": \"").append(esc(v.why())).append("\",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"principal\": \"").append(v.principal()).append("\",\n");
        b.append("        \"interest\": \"").append(v.interest()).append("\",\n");
        b.append("        \"percentage\": \"").append(v.percentage()).append("\",\n");
        b.append("        \"chargeCalculationTypeValue\": ").append(v.calcType()).append(",\n");
        b.append("        \"currencyCode\": \"MNT\",\n");
        b.append("        \"currencyDecimalPlaces\": 2,\n");
        b.append("        \"tenantId\": \"").append(tenantId).append("\",\n");
        b.append("        \"ambientRoundingModeOrdinal\": ")
                .append(c.ambientOrdinal() == null ? "null" : String.valueOf(c.ambientOrdinal())).append(",\n");
        b.append("        \"ambientRoundingModeIntent\": \"")
                .append(c.ambientOrdinal() == null ? "ABSENT" : RoundingMode.values()[c.ambientOrdinal()].name()).append("\",\n");
        b.append("        \"threadedRoundingModeOrdinal\": ").append(c.threadedOrdinal()).append(",\n");
        b.append("        \"threadedRoundingModeIntent\": \"").append(RoundingMode.values()[c.threadedOrdinal()].name())
                .append("\"\n");
        b.append("      },\n");
        b.append("      \"attestation\": {\n");
        b.append("        \"ambientMathContextObject\": \"").append(esc(ambientEcho)).append("\",\n");
        b.append("        \"threadedMathContextObject\": \"").append(mc).append("\",\n");
        b.append("        \"threadedPrecisionObject\": ").append(mc.getPrecision()).append(",\n");
        b.append("        \"threadedRoundingModeObject\": \"").append(mc.getRoundingMode().name()).append("\"\n");
        b.append("      },\n");

        String observed = null;
        String extra = null;
        String error = null;
        String stack = null;
        try {
            switch (c.leg().id()) {
                case "L1-calculateInstallmentCharge" -> {
                    final ProgressiveLoanScheduleGenerator g = newGenerator();
                    final LoanCharge lc = newLoanCharge(TIME_INSTALMENT_FEE, v.calcType(), v.percentage(), START);
                    // cumulative is seeded exactly as cumulativeFeeChargesDueWithin seeds it
                    // [ProgressiveLoanScheduleGenerator.java:388]: Money.zero(currency, mc).
                    final Money cumulative = Money.zero(currency, mc);
                    final PrincipalInterest pi = new PrincipalInterest(Money.of(currency, new BigDecimal(v.principal()), mc),
                            Money.of(currency, new BigDecimal(v.interest()), mc), null);
                    final Method m = ProgressiveLoanScheduleGenerator.class.getDeclaredMethod("calculateInstallmentCharge",
                            PrincipalInterest.class, Money.class, LoanCharge.class, MathContext.class);
                    m.setAccessible(true);
                    final Money out = (Money) m.invoke(g, pi, cumulative, lc, mc);
                    observed = out.getAmount().toPlainString();
                    extra = "resultMoneyMc=" + out.getMc();
                }
                case "L2-calculateSpecificDueDateChargeWithPercentage" -> {
                    final ProgressiveLoanScheduleGenerator g = newGenerator();
                    final LoanCharge lc = newLoanCharge(TIME_SPECIFIED_DUE_DATE, v.calcType(), v.percentage(), START);
                    final Money cumulative = Money.zero(currency, mc);
                    final Money principalDisbursed = Money.of(currency, new BigDecimal(v.principal()), mc);
                    final Money totalInterest = Money.of(currency, new BigDecimal(v.interest()), mc);
                    final Method m = ProgressiveLoanScheduleGenerator.class.getDeclaredMethod(
                            "calculateSpecificDueDateChargeWithPercentage", Money.class, Money.class, Money.class, LoanCharge.class,
                            MathContext.class);
                    m.setAccessible(true);
                    final Money out = (Money) m.invoke(g, principalDisbursed, totalInterest, cumulative, lc, mc);
                    observed = out.getAmount().toPlainString();
                    extra = "resultMoneyMc=" + out.getMc();
                }
                case "L3-downPaymentAmount" -> {
                    final LoanRepaymentScheduleModelData md = modelData(currency, new BigDecimal(v.principal()), true,
                            new BigDecimal(v.percentage()));
                    final LoanApplicationTerms terms = LoanApplicationTerms.assembleFrom(md, mc);
                    observed = terms.getDownPaymentAmount().getAmount().toPlainString();
                    extra = "principalAsAssembled=" + terms.getPrincipal().getAmount().toPlainString();
                }
                case "L4-generate-87-with-instalment-fee" -> {
                    final ProgressiveLoanScheduleGenerator g = newGenerator();
                    final LoanCharge lc = newLoanCharge(TIME_INSTALMENT_FEE, v.calcType(), v.percentage(), START);
                    final Set<LoanCharge> charges = new LinkedHashSet<>();
                    charges.add(lc);
                    final LoanRepaymentScheduleModelData md = modelData(currency, new BigDecimal(v.principal()), false, null);
                    final LoanApplicationTerms terms = LoanApplicationTerms.assembleFrom(md, mc);
                    final LoanScheduleModel model = g.generate(mc, terms, charges, null);
                    final StringBuilder fees = new StringBuilder();
                    int n = 0;
                    for (LoanScheduleModelPeriod p : model.getPeriods()) {
                        if (p.isRepaymentPeriod()) {
                            if (n > 0) {
                                fees.append(";");
                            }
                            fees.append(p.feeChargesDue() == null ? "null" : p.feeChargesDue().toPlainString());
                            n++;
                        }
                    }
                    observed = fees.toString();
                    extra = "repaymentPeriods=" + n;
                }
                case "L5-downPaymentAmount-ambient-ctor" -> {
                    final Object[] r = assembleFromLongOverload(currency, new BigDecimal(v.principal()), new BigDecimal(v.percentage()),
                            mc);
                    final LoanApplicationTerms terms = (LoanApplicationTerms) r[0];
                    observed = terms.getDownPaymentAmount().getAmount().toPlainString();
                    // SELF-VALIDATION of the positional argument fill: if either read-back
                    // disagrees, the indices were wrong and the observation is not this site's.
                    extra = "indexSelfCheck=" + r[1] + "; principalAsAssembled="
                            + terms.getPrincipal().getAmount().toPlainString() + "; pctAsAssembled="
                            + String.valueOf(terms.getDisbursedAmountPercentageForDownPayment());
                }
                default -> throw new IllegalStateException("unknown leg " + c.leg().id());
            }
        } catch (Throwable t) {
            Throwable e = t;
            while (e instanceof java.lang.reflect.InvocationTargetException ite && ite.getCause() != null) {
                e = ite.getCause();
            }
            final StringWriter sw = new StringWriter();
            e.printStackTrace(new PrintWriter(sw));
            error = e.getClass().getName() + ": " + esc(String.valueOf(e.getMessage()));
            stack = esc(sw.toString());
        }

        b.append("      \"extra\": ").append(extra == null ? "null" : "\"" + esc(extra) + "\"").append(",\n");
        b.append("      \"observed\": ").append(observed == null ? "null" : "\"" + esc(observed) + "\"").append(",\n");
        b.append("      \"error\": ").append(error == null ? "null" : "\"" + error + "\"").append(",\n");
        b.append("      \"stackTrace\": ").append(stack == null ? "null" : "\"" + stack + "\"").append("\n");
        b.append("    }");
        return b.toString();
    }

    /**
     * Reaches the AMBIENT down-payment constructor [LoanApplicationTerms.java:747, block :863-869]
     * through the public 76-parameter static factory at :609. Every argument is filled with its
     * TYPE DEFAULT (null / false / 0) except the four the site actually reads. The indices are
     * located positionally from the source and then TYPE-ASSERTED, and the returned terms object is
     * read back so a wrong index shows up as a self-check failure rather than as a wrong number.
     */
    static Object[] assembleFromLongOverload(CurrencyData currency, BigDecimal principal, BigDecimal downPaymentPct, MathContext mc)
            throws Exception {
        Method target = null;
        for (Method m : LoanApplicationTerms.class.getDeclaredMethods()) {
            if (m.getName().equals("assembleFrom") && m.getParameterCount() > 60) {
                if (target != null) {
                    throw new IllegalStateException("more than one >60-parameter assembleFrom overload");
                }
                target = m;
            }
        }
        if (target == null) {
            throw new IllegalStateException("no >60-parameter assembleFrom overload found");
        }
        final Class<?>[] pt = target.getParameterTypes();
        final int n = pt.length;
        final int I_CURRENCY = 0;
        final int I_PRINCIPAL = 15;
        final int I_TOLERANCE = 24;
        final int I_ENABLE_DP = 53;
        final int I_DP_PCT = 54;
        final StringBuilder chk = new StringBuilder("params=" + n);
        chk.append(" t[0]=").append(pt[I_CURRENCY].getSimpleName());
        chk.append(" t[15]=").append(pt[I_PRINCIPAL].getSimpleName());
        chk.append(" t[24]=").append(pt[I_TOLERANCE].getSimpleName());
        chk.append(" t[53]=").append(pt[I_ENABLE_DP].getSimpleName());
        chk.append(" t[54]=").append(pt[I_DP_PCT].getSimpleName());
        if (!pt[I_CURRENCY].getSimpleName().equals("CurrencyData") || !pt[I_PRINCIPAL].getSimpleName().equals("Money")
                || !pt[I_TOLERANCE].getSimpleName().equals("Money") || !pt[I_ENABLE_DP].getSimpleName().equals("Boolean")
                || !pt[I_DP_PCT].getSimpleName().equals("BigDecimal")) {
            throw new IllegalStateException("positional argument fill REFUSED -- parameter types at the assumed indices "
                    + "do not match: " + chk);
        }
        final Object[] args = new Object[n];
        for (int i = 0; i < n; i++) {
            if (pt[i] == boolean.class) {
                args[i] = Boolean.FALSE;
            } else if (pt[i] == int.class) {
                args[i] = 0;
            } else if (pt[i] == long.class) {
                args[i] = 0L;
            } else {
                args[i] = null;
            }
        }
        args[I_CURRENCY] = currency;
        args[I_PRINCIPAL] = Money.of(currency, principal, mc);
        args[I_TOLERANCE] = Money.zero(currency, mc);
        args[I_ENABLE_DP] = Boolean.TRUE;
        args[I_DP_PCT] = downPaymentPct;
        target.setAccessible(true);
        final Object terms = target.invoke(null, args);
        return new Object[] { terms, chk.toString() };
    }

    static LoanRepaymentScheduleModelData modelData(CurrencyData currency, BigDecimal principal, boolean downPaymentEnabled,
            BigDecimal downPaymentPct) {
        return new LoanRepaymentScheduleModelData(START, currency, principal, DISBURSE, 6, 1, "MONTHS", new BigDecimal("12"),
                downPaymentEnabled, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, downPaymentPct, null, null, false, null,
                InterestMethod.DECLINING_BALANCE, true, false);
    }

    public static void main(String[] args) throws Exception {
        initUnsafe();
        final List<Case> cs = cases();
        final StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"harness\": \"T50 CaptureT50Tier2 -- ambient vs threaded at the real call sites\",\n");
        sb.append("  \"oracleCommit\": \"426a23544e8426a38ae43ae404670a0a7e85b9eb\",\n");
        sb.append("  \"moneyHelperPrecisionConstant\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append("  \"ambientCanary\": \"").append(ambientCanary()).append("\",\n");
        sb.append("  \"caseCount\": ").append(cs.size()).append(",\n");
        sb.append("  \"cases\": [\n");
        for (int i = 0; i < cs.size(); i++) {
            sb.append(run(cs.get(i)));
            sb.append(i == cs.size() - 1 ? "\n" : ",\n");
        }
        sb.append("  ]\n}\n");
        System.out.println(sb);
    }
}
