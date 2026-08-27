/*
 * T42 -- WHICH MathContext ACTUALLY GOVERNS THE MONEY, observed on the Path A seam.
 *
 * Runs the PINNED reference oracle (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a) IN PROCESS
 * through the Path-A embeddable seam (DEC-1 section 3.2), and prints OBSERVED schedules as JSON.
 *
 * IT ASSERTS NOTHING AND PREDICTS NOTHING.  Every value printed is what the oracle emitted,
 * rendered with BigDecimal.toPlainString() -- never through a float, never rounded by this
 * harness, never scientific notation.
 *
 * WHY THIS EXISTS.  T39 finding N-3: forcing the tenant RoundingMode (which moves the AMBIENT
 * MoneyHelper MathContext) left all sixteen T39 blocks byte-identical, while forcing the
 * THREADED MathContext moved fifteen of sixteen.  T35/T36/T37 attested the production
 * MathContext partly via the ambient reading.  This harness settles, BY OBSERVATION, which
 * context governs which arithmetic step.
 *
 * THE EXPERIMENTAL DESIGN, and why it is stronger than T39's.
 *
 *   T39 varied the two contexts with GLOBAL -D overrides, one whole run per axis.  Here every
 *   case carries its OWN (ambient, threaded) pair and its OWN tenant identifier, so the two
 *   axes are varied INDEPENDENTLY inside a single payload and every comparison is within-run.
 *   MoneyHelper caches per tenant id [MoneyHelper.java:36-37, :91-93], so a unique tenant id
 *   per case makes the cases independent.
 *
 *   THE DECISIVE PROBE IS ABSENCE, NOT DIFFERENCE.  A rounding-mode flip can only be seen on a
 *   value that happens to sit on a rounding boundary; "nothing moved" is therefore weak
 *   evidence that the context was not read.  So the strongest cases here set a tenant into
 *   ThreadLocalContextUtil but NEVER call MoneyHelper.initializeTenantRoundingMode for it.
 *   MoneyHelper.getRoundingMode() then THROWS
 *       IllegalStateException: Rounding mode is not initialized for tenant: <id>
 *   [MoneyHelper.java:75-81, reached from getMathContext() :91-93].  So:
 *       - if the schedule still generates, the ambient context was PROVABLY never consulted;
 *       - if it throws, the ambient context IS consulted and the recorded stack trace names
 *         the exact line that consulted it.
 *   Either way the answer is an observation, not an inference.  The AMB-CANARY case proves the
 *   probe is live rather than vacuous: it reads MoneyHelper.getMathContext() itself on an
 *   uninitialised tenant and records the throw.
 *
 * CASE FAMILIES.
 *   T42-CAL      rig calibration at (12, HALF_UP) against the shipped USD test literal
 *                [EmbeddableProgressiveLoanScheduleGeneratorTest.java:44, :74-95].
 *                NEVER a parity vector.
 *   T42-CTL-*    reproduction controls against committed T39/T37/Q0a observations.
 *   T42-AMB-*    the ambient-absence probe and the ambient rounding-mode flip, over shapes
 *                chosen to REACH the sites that read the ambient context (down payment,
 *                installmentAmountInMultiplesOf, currency inMultiplesOf with 0 decimal
 *                places, fixedLength, ACTUAL days-in-year, drift, month-end).
 *   T42-THR-*    the threaded rounding-mode flip on the same shapes -- the behavioural
 *                discriminator.
 *   T42-PREC-*   T39 N-4: does threaded precision 19 separate from 12 on ANY shape?  Swept
 *                over principal magnitude, term length and rate.
 *
 * MONEY RULE.  Integer minor units, exact text, no float anywhere in this harness.
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

import java.io.PrintWriter;
import java.io.StringWriter;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class CaptureMathContext {

    /** Sentinel: do NOT initialise MoneyHelper for this case's tenant. */
    static final Integer AMBIENT_ABSENT = null;

    record Shape(String name, LocalDate startDate, LocalDate disbursementDate, BigDecimal principal, int noRepayments,
            BigDecimal annualRate, String currencyCode, int currencyDigits, Integer currencyInMultiplesOf, DaysInMonthType dim,
            DaysInYearType diy, DaysInYearCustomStrategyType diyCustom, BigDecimal downPaymentPct,
            Integer installmentMultiplesOf, Integer fixedLength, boolean interestRecognitionOnDisbursementDate,
            boolean allowPartialPeriodInterestCalculation, boolean allowFullTermForTranche) {
    }

    record Case(String id, String family, String purpose, Shape shape, int precision, RoundingMode mode,
            Integer tenantRoundingMode, String tenantTimeZone) {
    }

    // ---- shape constructors -------------------------------------------------------------

    /** The ratified production shape family: MNT, 2 dp, 30/360, monthly, declining balance. */
    static Shape mnt(String name, LocalDate start, LocalDate disb, String principal, int n, String rate) {
        return new Shape(name, start, disb, new BigDecimal(principal), n, new BigDecimal(rate), "MNT", 2, null,
                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null, BigDecimal.ZERO, null, null, false, true, false);
    }

    static Shape withDownPayment(Shape s, String pct) {
        return new Shape(s.name(), s.startDate(), s.disbursementDate(), s.principal(), s.noRepayments(), s.annualRate(),
                s.currencyCode(), s.currencyDigits(), s.currencyInMultiplesOf(), s.dim(), s.diy(), s.diyCustom(),
                new BigDecimal(pct), s.installmentMultiplesOf(), s.fixedLength(), s.interestRecognitionOnDisbursementDate(),
                s.allowPartialPeriodInterestCalculation(), s.allowFullTermForTranche());
    }

    static Shape withInstallmentMultiplesOf(Shape s, Integer m) {
        return new Shape(s.name(), s.startDate(), s.disbursementDate(), s.principal(), s.noRepayments(), s.annualRate(),
                s.currencyCode(), s.currencyDigits(), s.currencyInMultiplesOf(), s.dim(), s.diy(), s.diyCustom(),
                s.downPaymentPct(), m, s.fixedLength(), s.interestRecognitionOnDisbursementDate(),
                s.allowPartialPeriodInterestCalculation(), s.allowFullTermForTranche());
    }

    static Shape withCurrency(Shape s, String code, int digits, Integer inMultiplesOf) {
        return new Shape(s.name(), s.startDate(), s.disbursementDate(), s.principal(), s.noRepayments(), s.annualRate(), code,
                digits, inMultiplesOf, s.dim(), s.diy(), s.diyCustom(), s.downPaymentPct(), s.installmentMultiplesOf(),
                s.fixedLength(), s.interestRecognitionOnDisbursementDate(), s.allowPartialPeriodInterestCalculation(),
                s.allowFullTermForTranche());
    }

    static Shape withDaysInYear(Shape s, DaysInYearType diy) {
        return new Shape(s.name(), s.startDate(), s.disbursementDate(), s.principal(), s.noRepayments(), s.annualRate(),
                s.currencyCode(), s.currencyDigits(), s.currencyInMultiplesOf(), s.dim(), diy, s.diyCustom(),
                s.downPaymentPct(), s.installmentMultiplesOf(), s.fixedLength(), s.interestRecognitionOnDisbursementDate(),
                s.allowPartialPeriodInterestCalculation(), s.allowFullTermForTranche());
    }

    static Shape withDaysInMonth(Shape s, DaysInMonthType dim) {
        return new Shape(s.name(), s.startDate(), s.disbursementDate(), s.principal(), s.noRepayments(), s.annualRate(),
                s.currencyCode(), s.currencyDigits(), s.currencyInMultiplesOf(), dim, s.diy(), s.diyCustom(),
                s.downPaymentPct(), s.installmentMultiplesOf(), s.fixedLength(), s.interestRecognitionOnDisbursementDate(),
                s.allowPartialPeriodInterestCalculation(), s.allowFullTermForTranche());
    }

    static Shape withFixedLength(Shape s, Integer fixedLength) {
        return new Shape(s.name(), s.startDate(), s.disbursementDate(), s.principal(), s.noRepayments(), s.annualRate(),
                s.currencyCode(), s.currencyDigits(), s.currencyInMultiplesOf(), s.dim(), s.diy(), s.diyCustom(),
                s.downPaymentPct(), s.installmentMultiplesOf(), fixedLength, s.interestRecognitionOnDisbursementDate(),
                s.allowPartialPeriodInterestCalculation(), s.allowFullTermForTranche());
    }

    static Shape withInterestRecognitionOnDisbursementDate(Shape s, boolean v) {
        return new Shape(s.name(), s.startDate(), s.disbursementDate(), s.principal(), s.noRepayments(), s.annualRate(),
                s.currencyCode(), s.currencyDigits(), s.currencyInMultiplesOf(), s.dim(), s.diy(), s.diyCustom(),
                s.downPaymentPct(), s.installmentMultiplesOf(), s.fixedLength(), v,
                s.allowPartialPeriodInterestCalculation(), s.allowFullTermForTranche());
    }

    static Shape rename(Shape s, String name) {
        return new Shape(name, s.startDate(), s.disbursementDate(), s.principal(), s.noRepayments(), s.annualRate(),
                s.currencyCode(), s.currencyDigits(), s.currencyInMultiplesOf(), s.dim(), s.diy(), s.diyCustom(),
                s.downPaymentPct(), s.installmentMultiplesOf(), s.fixedLength(), s.interestRecognitionOnDisbursementDate(),
                s.allowPartialPeriodInterestCalculation(), s.allowFullTermForTranche());
    }

    // ---- the shapes under test ------------------------------------------------------------

    /**
     * Shapes chosen so that between them they REACH every ambient-context read the static scan
     * of the pinned source found on the Path A call graph, and the T39 shapes as controls.
     */
    static List<Shape> ambientProbeShapes() {
        final List<Shape> out = new ArrayList<>();
        final Shape base = mnt("plain", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6");
        out.add(base);
        // the T39 drift shape and the T39 month-end shape -- the two families already captured
        out.add(mnt("drift", LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6"));
        out.add(mnt("monthEnd", LocalDate.of(2024, 1, 31), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6"));
        // down payment: ProgressiveLoanScheduleGenerator.java:331-337
        out.add(rename(withDownPayment(base, "25"), "downPayment25"));
        // a down-payment percentage whose product is NOT exact at 2 dp -- rounding-boundary bait
        out.add(rename(withDownPayment(mnt("x", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1000001", 6, "21.6"), "33.333"),
                "downPaymentAwkward"));
        // installmentAmountInMultiplesOf: Money.roundToMultiplesOf(Money,Integer,MathContext)
        // ends in the TWO-argument Money.of, i.e. the ambient context [Money.java:161-171]
        out.add(rename(withInstallmentMultiplesOf(withDownPayment(base, "33.333"), 1000), "downPaymentMultiples1000"));
        out.add(rename(withInstallmentMultiplesOf(base, 1000), "multiples1000"));
        // currency with 0 decimal places AND inMultiplesOf -> Money's constructor takes the
        // ambient roundToMultiplesOf(BigDecimal,Integer) branch [Money.java:49-52, :152-158]
        out.add(rename(withCurrency(withInstallmentMultiplesOf(base, 100), "MNT", 0, 100), "zeroDpMultiples100"));
        out.add(rename(withCurrency(withDownPayment(withInstallmentMultiplesOf(base, 100), "33.333"), "MNT", 0, 100),
                "zeroDpMultiples100DownPayment"));
        // fixedLength
        out.add(rename(withFixedLength(base, 6), "fixedLength6"));
        // ACTUAL days in year / days in month -- different rate-factor arms
        out.add(rename(withDaysInYear(base, DaysInYearType.ACTUAL), "daysInYearActual"));
        out.add(rename(withDaysInMonth(withDaysInYear(base, DaysInYearType.ACTUAL), DaysInMonthType.ACTUAL), "actualActual"));
        // interest recognition on disbursement date
        out.add(rename(withInterestRecognitionOnDisbursementDate(base, true), "interestRecognitionOnDisb"));
        return out;
    }

    /**
     * T39 N-4: is there ANY shape on which threaded precision 19 separates from 12?
     *
     * The mechanism the search targets is transcribed, not guessed: the rate factor is
     * .setScale(mc.getPrecision(), mc.getRoundingMode()) at
     * ProgressiveEMICalculator.java:1962 and :1979, i.e. the precision acts as an ABSOLUTE
     * SCALE on a quantity of order 1e-2.  The truncated residual is therefore of order
     * 10^-precision, and it can only reach a minor unit once the outstanding balance is of
     * order 10^precision-2.  So the search sweeps principal magnitude by decades, and sweeps
     * term length and rate to let the residual accumulate.
     */
    static List<Shape> precisionProbeShapes() {
        final List<Shape> out = new ArrayList<>();
        final String[] principals = { "1200000", "50000000", "1000000000", "10000000000", "100000000000", "1000000000000",
                "10000000000000", "100000000000000" };
        for (String p : principals) {
            out.add(mnt("p" + p.length() + "_n6_r21.6", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), p, 6, "21.6"));
            out.add(mnt("p" + p.length() + "_n36_r21.6", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), p, 36, "21.6"));
            out.add(mnt("p" + p.length() + "_n360_r7.7", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), p, 360, "7.7"));
            // a rate whose /1200 has a non-terminating expansion, so the setScale actually cuts
            out.add(mnt("p" + p.length() + "_n36_r13", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), p, 36, "13"));
            // inside the drift region, where periodRatio is itself a non-terminating quotient
            out.add(mnt("p" + p.length() + "_drift_n36_r21.6", LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), p, 36, "21.6"));
            // ACTUAL/ACTUAL -- the other rate-factor arm, quotients by 365/366
            out.add(rename(withDaysInMonth(withDaysInYear(
                    mnt("x", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), p, 36, "13"), DaysInYearType.ACTUAL),
                    DaysInMonthType.ACTUAL), "p" + p.length() + "_actualActual_n36_r13"));
        }
        return out;
    }

    static List<Case> cases() {
        final List<Case> cases = new ArrayList<>();
        final String tz = "Asia/Ulaanbaatar";

        // ---- RIG CALIBRATION ----------------------------------------------------------
        // Must reproduce the shipped USD literal digit for digit.  NOT a parity vector.
        cases.add(new Case("T42-CAL", "CALIBRATION",
                "RIG CALIBRATION at threaded (12, HALF_UP), ambient HALF_UP, vs the shipped USD test literal",
                new Shape("cal", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("100"), 6,
                        new BigDecimal("7.0"), "usd", 2, null, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                        BigDecimal.ZERO, null, null, false, true, false),
                12, RoundingMode.HALF_UP, 4, tz));

        // ---- REPRODUCTION CONTROLS ----------------------------------------------------
        cases.add(new Case("T42-CTL-Q0a", "CONTROL",
                "REPRODUCTION CONTROL vs committed observations Q0a / T37-CTL-Q0a / T39-CTL-Q0a",
                mnt("ctlQ0a", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6"), 19,
                RoundingMode.HALF_UP, 4, tz));
        cases.add(new Case("T42-CTL-1", "CONTROL", "REPRODUCTION CONTROL vs committed captures T37-3-A / T39-CTL-1",
                mnt("ctl1", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1014632", 6, "7.0"), 19, RoundingMode.HALF_UP,
                4, tz));
        cases.add(new Case("T42-CTL-P0A", "CONTROL", "REPRODUCTION CONTROL vs committed capture T39-P0-A (drift)",
                mnt("ctlP0A", LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6"), 19,
                RoundingMode.HALF_UP, 4, tz));
        cases.add(new Case("T42-CTL-MEB", "CONTROL", "REPRODUCTION CONTROL vs committed capture T39-ME-B (month end)",
                mnt("ctlMEB", LocalDate.of(2024, 1, 31), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6"), 19,
                RoundingMode.HALF_UP, 4, tz));

        // ---- THE AMBIENT / THREADED MATRIX --------------------------------------------
        // For every probe shape, four cases that vary the two contexts INDEPENDENTLY:
        //   A  ambient HALF_UP(4), threaded (19, HALF_UP)   <- the ratified production pair
        //   B  ambient DOWN(1),    threaded (19, HALF_UP)   <- ambient moved, threaded fixed
        //   C  ambient HALF_UP(4), threaded (19, DOWN)      <- threaded moved, ambient fixed
        //   D  ambient ABSENT,     threaded (19, HALF_UP)   <- the absence probe
        int i = 0;
        for (Shape s : ambientProbeShapes()) {
            final String n = String.format("%02d", i++);
            cases.add(new Case("T42-MX-" + n + "-A", "MATRIX",
                    "shape " + s.name() + " | ambient HALF_UP(4) | threaded (19, HALF_UP) -- the ratified pair", s, 19,
                    RoundingMode.HALF_UP, 4, tz));
            cases.add(new Case("T42-MX-" + n + "-B", "MATRIX",
                    "shape " + s.name() + " | ambient DOWN(1) | threaded (19, HALF_UP) -- AMBIENT moved alone", s, 19,
                    RoundingMode.HALF_UP, 1, tz));
            cases.add(new Case("T42-MX-" + n + "-C", "MATRIX",
                    "shape " + s.name() + " | ambient HALF_UP(4) | threaded (19, DOWN) -- THREADED moved alone", s, 19,
                    RoundingMode.DOWN, 4, tz));
            cases.add(new Case("T42-MX-" + n + "-D", "MATRIX",
                    "shape " + s.name() + " | ambient ABSENT (MoneyHelper never initialised) | threaded (19, HALF_UP)"
                            + " -- the ABSENCE probe",
                    s, 19, RoundingMode.HALF_UP, AMBIENT_ABSENT, tz));
            cases.add(new Case("T42-MX-" + n + "-E", "MATRIX",
                    "shape " + s.name() + " | ambient UP(0) | threaded (19, HALF_UP) -- AMBIENT moved alone, second mode", s,
                    19, RoundingMode.HALF_UP, 0, tz));
        }

        // ---- THE PRECISION SEARCH -----------------------------------------------------
        // For every precision shape, threaded precision 19 vs 12 vs 8, ambient held at the
        // ratified HALF_UP so the ONLY variable is the threaded precision.
        int j = 0;
        for (Shape s : precisionProbeShapes()) {
            final String n = String.format("%02d", j++);
            cases.add(new Case("T42-PREC-" + n + "-p19", "PRECISION",
                    "shape " + s.name() + " | threaded (19, HALF_UP) | ambient HALF_UP(4)", s, 19, RoundingMode.HALF_UP, 4,
                    tz));
            cases.add(new Case("T42-PREC-" + n + "-p12", "PRECISION",
                    "shape " + s.name() + " | threaded (12, HALF_UP) | ambient HALF_UP(4)", s, 12, RoundingMode.HALF_UP, 4,
                    tz));
            cases.add(new Case("T42-PREC-" + n + "-p8", "PRECISION",
                    "shape " + s.name() + " | threaded (8, HALF_UP) | ambient HALF_UP(4)", s, 8, RoundingMode.HALF_UP, 4, tz));
        }

        return cases;
    }

    public static void main(String[] args) {
        final List<Case> cases = cases();

        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"task\": \"T42\",\n");
        sb.append("  \"harness\": \"CaptureMathContext.java\",\n");
        sb.append("  \"question\": \"T42(a): which MathContext governs which arithmetic step?  T42(b): does threaded precision 19 separate from 12 on any shape?\",\n");
        sb.append("  \"path\": \"A -- embeddable seam, in-process, no server, no database\",\n");
        sb.append("  \"fineractCommit\": \"426a23544e8426a38ae43ae404670a0a7e85b9eb\",\n");
        sb.append("  \"moneyHelperPrecisionConstant\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append("  \"javaVersion\": \"").append(System.getProperty("java.version")).append("\",\n");
        sb.append("  \"javaVmName\": \"").append(System.getProperty("java.vm.name")).append("\",\n");
        sb.append("  \"javaVmVersion\": \"").append(System.getProperty("java.vm.version")).append("\",\n");
        sb.append("  \"javaVendor\": \"").append(System.getProperty("java.vendor")).append("\",\n");
        sb.append("  \"jvmUserTimezone\": \"").append(System.getProperty("user.timezone")).append("\",\n");
        sb.append("  \"jvmFileEncoding\": \"").append(System.getProperty("file.encoding")).append("\",\n");
        sb.append("  \"ambientCanary\": ").append(ambientCanary()).append(",\n");
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

    /**
     * Proves the ABSENCE PROBE IS LIVE, not vacuous.  Sets a tenant that MoneyHelper was never
     * initialised for and reads the ambient context directly.  If this does NOT throw, every
     * "-D" (absence) case below is meaningless and the run must be rejected.
     */
    static String ambientCanary() {
        final String tenantId = "t42_canary_never_initialised";
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenantId, tenantId, "Asia/Ulaanbaatar", null));
        String result;
        try {
            result = "\"NO THROW -- ambient read succeeded: " + MoneyHelper.getMathContext() + "\"";
        } catch (RuntimeException e) {
            result = "\"THREW " + e.getClass().getName() + ": " + String.valueOf(e.getMessage()).replace("\"", "'") + "\"";
        }
        return result;
    }

    static String run(final Case c) {
        final Shape s = c.shape();
        // A UNIQUE tenant id per case.  MoneyHelper caches per tenant id, so this makes the
        // cases independent and lets the ABSENCE cases have a genuinely uninitialised tenant.
        final String tenantId = "t42_" + c.id().toLowerCase().replace('-', '_');
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenantId, tenantId, c.tenantTimeZone(), null));
        if (c.tenantRoundingMode() != null) {
            MoneyHelper.initializeTenantRoundingMode(tenantId, c.tenantRoundingMode());
        }
        String ambientMathContext;
        try {
            ambientMathContext = String.valueOf(MoneyHelper.getMathContext());
        } catch (RuntimeException e) {
            ambientMathContext = "THREW " + e.getClass().getName() + ": " + String.valueOf(e.getMessage()).replace("\"", "'");
        }
        // Reading the ambient context above POPULATES MoneyHelper's cache for an initialised
        // tenant; for an ABSENT case it throws and leaves the cache empty, which is what the
        // probe needs.  Verified by the ambientCanary above.

        final MathContext mc = new MathContext(c.precision(), c.mode());
        final EmbeddableProgressiveLoanScheduleGenerator generator = new EmbeddableProgressiveLoanScheduleGenerator();
        final CurrencyData currency = new CurrencyData(s.currencyCode(), s.currencyCode(), s.currencyDigits(),
                s.currencyInMultiplesOf(), s.currencyCode(), s.currencyCode());

        final LoanRepaymentScheduleModelData config = new LoanRepaymentScheduleModelData(s.startDate(), currency,
                s.principal(), s.disbursementDate(), s.noRepayments(), 1, "MONTHS", s.annualRate(),
                BigDecimal.ZERO.compareTo(s.downPaymentPct()) != 0, s.dim(), s.diy(), s.downPaymentPct(),
                s.installmentMultiplesOf(), s.fixedLength(), s.interestRecognitionOnDisbursementDate(), s.diyCustom(),
                InterestMethod.DECLINING_BALANCE, s.allowPartialPeriodInterestCalculation(), s.allowFullTermForTranche());

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"family\": \"").append(c.family()).append("\",\n");
        b.append("      \"shape\": \"").append(s.name()).append("\",\n");
        b.append("      \"purpose\": \"").append(c.purpose()).append("\",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"scheduleGenerationStartDate\": \"").append(s.startDate()).append("\",\n");
        b.append("        \"disbursementDate\": \"").append(s.disbursementDate()).append("\",\n");
        b.append("        \"disbursementAmount\": \"").append(s.principal().toPlainString()).append("\",\n");
        b.append("        \"numberOfRepayments\": ").append(s.noRepayments()).append(",\n");
        b.append("        \"repaymentEvery\": 1,\n");
        b.append("        \"repaymentFrequencyType\": \"MONTHS\",\n");
        b.append("        \"annualNominalInterestRate\": \"").append(s.annualRate().toPlainString()).append("\",\n");
        b.append("        \"threadedMathContextPrecision\": ").append(c.precision()).append(",\n");
        b.append("        \"threadedMathContextRoundingMode\": \"").append(c.mode()).append("\",\n");
        b.append("        \"tenantId\": \"").append(tenantId).append("\",\n");
        b.append("        \"tenantTimeZone\": \"").append(c.tenantTimeZone()).append("\",\n");
        b.append("        \"tenantRoundingModeOrdinal\": ")
                .append(c.tenantRoundingMode() == null ? "null" : c.tenantRoundingMode()).append(",\n");
        b.append("        \"ambientMoneyHelperMathContext\": \"").append(ambientMathContext).append("\",\n");
        b.append("        \"currencyCode\": \"").append(s.currencyCode()).append("\",\n");
        b.append("        \"currencyDecimalPlaces\": ").append(s.currencyDigits()).append(",\n");
        b.append("        \"currencyInMultiplesOf\": ").append(s.currencyInMultiplesOf()).append(",\n");
        b.append("        \"daysInMonth\": \"").append(s.dim()).append("\",\n");
        b.append("        \"daysInYear\": \"").append(s.diy()).append("\",\n");
        b.append("        \"daysInYearCustomStrategy\": ")
                .append(s.diyCustom() == null ? "null" : "\"" + s.diyCustom() + "\"").append(",\n");
        b.append("        \"downPaymentEnabled\": ")
                .append(BigDecimal.ZERO.compareTo(s.downPaymentPct()) != 0).append(",\n");
        b.append("        \"downPaymentPercentage\": \"").append(s.downPaymentPct().toPlainString()).append("\",\n");
        b.append("        \"installmentAmountInMultiplesOf\": ").append(s.installmentMultiplesOf()).append(",\n");
        b.append("        \"fixedLength\": ").append(s.fixedLength()).append(",\n");
        b.append("        \"interestRecognitionOnDisbursementDate\": ")
                .append(s.interestRecognitionOnDisbursementDate()).append(",\n");
        b.append("        \"interestMethod\": \"DECLINING_BALANCE\",\n");
        b.append("        \"allowPartialPeriodInterestCalculation\": ")
                .append(s.allowPartialPeriodInterestCalculation()).append(",\n");
        b.append("        \"allowFullTermForTranche\": ").append(s.allowFullTermForTranche()).append("\n");
        b.append("      },\n");

        final LoanSchedulePlan plan;
        try {
            plan = generator.generate(mc, config);
        } catch (RuntimeException | StackOverflowError e) {
            final StringWriter sw = new StringWriter();
            e.printStackTrace(new PrintWriter(sw));
            b.append("      \"observed\": null,\n");
            b.append("      \"error\": \"").append(e.getClass().getName()).append(": ")
                    .append(String.valueOf(e.getMessage()).replace("\\", "\\\\").replace("\"", "'").replace("\n", " "))
                    .append("\",\n");
            b.append("      \"stackTrace\": [\n");
            final List<String> frames = new ArrayList<>();
            for (String line : sw.toString().split("\n")) {
                frames.add("        \"" + line.trim().replace("\\", "\\\\").replace("\"", "'") + "\"");
            }
            b.append(String.join(",\n", frames)).append("\n");
            b.append("      ]\n");
            b.append("    }");
            return b.toString();
        }

        b.append("      \"observed\": {\n");
        b.append("        \"loanTermInDays\": ").append(plan.getLoanTermInDays()).append(",\n");
        b.append("        \"totalDisbursedAmount\": \"").append(pl(plan.getTotalDisbursedAmount())).append("\",\n");
        b.append("        \"totalInterestAmount\": \"").append(pl(plan.getTotalInterestAmount())).append("\",\n");
        b.append("        \"totalRepaymentAmount\": \"").append(pl(plan.getTotalRepaymentAmount())).append("\",\n");
        b.append("        \"periods\": [\n");

        final List<String> rows = new ArrayList<>();
        for (LoanSchedulePlanPeriod period : plan.getPeriods()) {
            if (period instanceof LoanSchedulePlanDisbursementPeriod dp) {
                rows.add("          {\"type\": \"DISBURSEMENT\", \"fromDate\": \"" + dp.periodFromDate()
                        + "\", \"dueDate\": \"" + dp.periodDueDate() + "\", \"principal\": \""
                        + pl(dp.getPrincipalAmount()) + "\"}");
            } else if (period instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                rows.add("          {\"type\": \"DOWN_PAYMENT\", \"periodNumber\": " + dpp.periodNumber()
                        + ", \"fromDate\": \"" + dpp.periodFromDate() + "\", \"dueDate\": \"" + dpp.periodDueDate()
                        + "\", \"balance\": \"" + pl(dpp.getOutstandingLoanBalance()) + "\", \"principal\": \""
                        + pl(dpp.getPrincipalAmount()) + "\", \"total\": \"" + pl(dpp.getTotalDueAmount())
                        + "\", \"totalOutstandingBalance\": \"" + pl(dpp.getTotalOutstandingLoanBalance()) + "\"}");
            } else if (period instanceof LoanSchedulePlanRepaymentPeriod rp) {
                rows.add("          {\"type\": \"REPAYMENT\", \"periodNumber\": " + rp.periodNumber()
                        + ", \"fromDate\": \"" + rp.periodFromDate() + "\", \"dueDate\": \"" + rp.periodDueDate()
                        + "\", \"balance\": \"" + pl(rp.getOutstandingLoanBalance()) + "\", \"principal\": \""
                        + pl(rp.getPrincipalAmount()) + "\", \"interest\": \"" + pl(rp.getInterestAmount())
                        + "\", \"fee\": \"" + pl(rp.getFeeAmount()) + "\", \"penalty\": \""
                        + pl(rp.getPenaltyAmount()) + "\", \"total\": \"" + pl(rp.getTotalDueAmount())
                        + "\", \"totalOutstandingBalance\": \"" + pl(rp.getTotalOutstandingLoanBalance()) + "\"}");
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

    /** Plain string, never scientific notation, never a float. */
    static String pl(final BigDecimal v) {
        return v == null ? "null" : v.toPlainString();
    }
}
