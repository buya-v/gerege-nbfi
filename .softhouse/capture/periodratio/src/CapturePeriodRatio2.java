/*
 * T46 -- corrections pass over the T39 periodRatio capture set.
 *
 * Runs the PINNED reference oracle (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a) IN PROCESS
 * through the Path-A embeddable seam, and prints OBSERVED schedules as JSON.
 *
 * IT ASSERTS NOTHING AND PREDICTS NOTHING.  Every value printed is what the oracle emitted,
 * rendered with BigDecimal.toPlainString() -- never through a float, never rounded by this
 * harness, never scientific notation.  No expected value is synthesised here.
 *
 * WHY THIS EXISTS -- two T44 findings against T39:
 *
 *   F39-3  "the threaded MathContext is echoed as INTENT, not as the object".  T39 wrote the
 *          case record's own precision()/mode() fields into the payload; nothing read `mc`.
 *          T42's ratified rule 2 requires the OBJECT.  This harness echoes
 *          mc.toString() / mc.getPrecision() / mc.getRoundingMode() off the reference that is
 *          handed to generate(), under `threadedMathContext*` keys, AND keeps T39's original
 *          intent keys unchanged so the re-emission can be proved value-for-value identical.
 *
 *   F39-2  the attestation's "two independent witnesses" were one ambient cache write logged
 *          and read back.  Corrected in ../ATTESTATION-T46.md; this harness additionally
 *          records an explicit `wiring` field naming the object handed to the callee.
 *
 * TWO CASE SETS, selected with -Dt46.set:
 *
 *   -Dt46.set=reemit   (default)  the SIXTEEN T39 cases, input for input, same ids.  Its only
 *                      purpose is the identity proof required by .softhouse/patterns.md
 *                      ("re-emit input-for-input BEFORE you add cases").  No new case appears
 *                      in this set.
 *
 *   -Dt46.set=arms     NEW cases with NEW ids, in a SEPARATE pass, exercising
 *                      calculatePeriodRatio's YEARS / WEEKS / DAYS arms
 *                      (ProgressiveEMICalculator.java:1405, :1407, :1408) -- the arms T44
 *                      recorded as "entirely uncaptured".  T46-YR-* are expected to reach
 *                      calculateRateFactorPerPeriodBasedOnRepaymentFrequency's `default ->
 *                      throw new UnsupportedOperationException("Invalid repayment frequency")`
 *                      at :1609; whether they do is an OBSERVATION, and this harness records
 *                      whatever comes back, including the throw.
 *
 * SETTINGS.  Everything except the rig calibration runs at the ratified production
 * MathContext (19, HALF_UP).  MoneyHelper.PRECISION = 19 is a compile-time constant
 * [MoneyHelper.java:35, :91-93] and HALF_UP is RoundingMode ordinal 4.
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

public class CapturePeriodRatio2 {

    record Case(String id, String family, String purpose, LocalDate startDate,
            LocalDate disbursementDate, BigDecimal principal, int noRepayments, BigDecimal annualRate,
            int precision, RoundingMode mode, String currencyCode, int currencyDigits, DaysInMonthType dim,
            DaysInYearType diy, DaysInYearCustomStrategyType diyCustom, BigDecimal downPaymentPct,
            Integer installmentMultiplesOf, Integer fixedLength, boolean interestRecognitionOnDisbursementDate,
            boolean allowPartialPeriodInterestCalculation, boolean allowFullTermForTranche, String tenantId,
            Integer tenantRoundingMode, String tenantTimeZone, String repaymentFrequencyType, int repaymentEvery) {
    }

    /** A case at the ratified production settings, monthly -- byte-for-byte T39's prod(). */
    static Case prod(String id, String family, String purpose, LocalDate start, LocalDate disb,
            String principal, int noRepayments, String rate, String tenantId) {
        return new Case(id, family, purpose, start, disb, new BigDecimal(principal), noRepayments,
                new BigDecimal(rate), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360, null, BigDecimal.ZERO, null, null, false, true, false, tenantId, 4,
                "Asia/Ulaanbaatar", "MONTHS", 1);
    }

    /** As prod(), but with an explicit repayment frequency and repaymentEvery. */
    static Case freq(String id, String family, String purpose, LocalDate start, LocalDate disb,
            String principal, int noRepayments, String rate, String tenantId, String frequency, int every) {
        return new Case(id, family, purpose, start, disb, new BigDecimal(principal), noRepayments,
                new BigDecimal(rate), 19, RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360, null, BigDecimal.ZERO, null, null, false, true, false, tenantId, 4,
                "Asia/Ulaanbaatar", frequency, every);
    }

    // ------------------------------------------------------------------------------------
    // SET 1 -- the RE-EMISSION.  Sixteen cases, input for input identical to T39's cases().
    // Any edit here voids the identity proof.
    // ------------------------------------------------------------------------------------
    static List<Case> reemitCases() {
        final List<Case> cases = new ArrayList<>();

        cases.add(new Case("T39-CAL", "CALIBRATION",
                "RIG CALIBRATION at (12, HALF_UP) vs the shipped USD test literal",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("100"), 6,
                new BigDecimal("7.0"), 12, RoundingMode.HALF_UP, "usd", 2, DaysInMonthType.DAYS_30,
                DaysInYearType.DAYS_360, null, BigDecimal.ZERO, null, null, false, true, false, "t39_cal", 4,
                "Asia/Ulaanbaatar", "MONTHS", 1));

        cases.add(prod("T39-CTL-Q0a", "CONTROL",
                "REPRODUCTION CONTROL vs committed observation Q0a and capture T37-CTL-Q0a",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6", "t39_ctl_q0a"));
        cases.add(prod("T39-CTL-1", "CONTROL",
                "in-graded-domain control OUTSIDE the drift region; reproduces capture T37-3-A",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1014632", 6, "7.0", "t39_ctl_1"));
        cases.add(prod("T39-CTL-2", "CONTROL",
                "in-graded-domain control OUTSIDE the drift region, mid-month start = disbursement",
                LocalDate.of(2024, 1, 15), LocalDate.of(2024, 1, 15), "1200000", 6, "21.6", "t39_ctl_2"));

        cases.add(prod("T39-P0-A", "DRIFT",
                "T34 section 1.4's named candidate shape: start 28 Jan, disbursement 31 Jan",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6", "t39_p0_a"));
        cases.add(prod("T39-P0-B", "DRIFT",
                "T34 section 1.3's hand-worked shape: start 28 Jan, disbursement 29 Jan",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 29), "1200000", 6, "21.6", "t39_p0_b"));
        cases.add(prod("T39-P0-C", "DRIFT", "drift over 12 periods, start 29 Jan",
                LocalDate.of(2024, 1, 29), LocalDate.of(2024, 1, 31), "5000000", 12, "16.8", "t39_p0_c"));
        cases.add(prod("T39-P0-D", "DRIFT",
                "T34 section 1.4's WORST re-derived gap: 36 periods, MNT 50,000,000",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "50000000", 36, "21.6", "t39_p0_d"));
        cases.add(prod("T39-P0-E", "DRIFT", "drift in a COMMON year (2025), start 28 Jan",
                LocalDate.of(2025, 1, 28), LocalDate.of(2025, 1, 31), "1200000", 6, "21.6", "t39_p0_e"));
        cases.add(prod("T39-P0-F", "DRIFT",
                "drift on the SMALLEST principal, MNT 100 -- is there a size threshold?",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "100", 6, "21.6", "t39_p0_f"));
        cases.add(prod("T39-P0-G", "DRIFT", "drift seeded in MARCH, not January",
                LocalDate.of(2024, 3, 28), LocalDate.of(2024, 3, 31), "2500000", 6, "16.8", "t39_p0_g"));
        cases.add(prod("T39-P0-H", "DRIFT", "drift seeded in a 30-DAY month (November)",
                LocalDate.of(2024, 11, 28), LocalDate.of(2024, 11, 30), "3000000", 6, "16.8", "t39_p0_h"));

        cases.add(prod("T39-ME-A", "MONTH_END",
                "month-end special case fires on periods 2,4,6; ALSO reproduces capture T37-3b-2",
                LocalDate.of(2024, 1, 31), LocalDate.of(2024, 1, 31), "3924149", 6, "16.8", "t39_me_a"));
        cases.add(prod("T39-ME-B", "MONTH_END", "month-end special case, 31 Jan seed, 21.6 %",
                LocalDate.of(2024, 1, 31), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6", "t39_me_b"));
        cases.add(prod("T39-ME-C", "MONTH_END", "month-end special case in a COMMON year (2023)",
                LocalDate.of(2023, 1, 31), LocalDate.of(2023, 1, 31), "1200000", 6, "21.6", "t39_me_c"));
        cases.add(prod("T39-ME-D", "MONTH_END",
                "month-end special case fires on ONE period only, 30 Jan seed",
                LocalDate.of(2024, 1, 30), LocalDate.of(2024, 1, 30), "1200000", 6, "21.6", "t39_me_d"));
        return cases;
    }

    // ------------------------------------------------------------------------------------
    // SET 2 -- NEW cases, NEW ids, a SEPARATE pass.  calculatePeriodRatio's non-MONTHS arms.
    //
    // T44's blind-spot list for this set: "calculatePeriodRatio's YEARS, WEEKS, DAYS arms
    // (:1405, :1407, :1408) -- entirely uncaptured", and F39-1(c) proposed them as the place
    // a packed-vs-naive discriminator would have to come from.  These cases put that to the
    // oracle.  T46-YR-A/B are the shapes on which packed and naive whole-YEARS disagree
    // (Feb-29 seed, Feb-28 target -- the only family on which ChronoUnit.YEARS.between and
    // "plusYears, step back on overshoot" differ).
    // ------------------------------------------------------------------------------------
    static List<Case> armsCases() {
        final List<Case> cases = new ArrayList<>();

        // --- CONTROL: the same monthly shape as T39-CTL-Q0a, re-taken through THIS harness,
        //     so the arms set is bracketed by a case whose value is already published.
        cases.add(prod("T46-ARM-CTL", "CONTROL",
                "monthly control identical to T39-CTL-Q0a, so this pass is comparable to T39's",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6", "t46_arm_ctl"));

        // --- YEARS arm (:1405).  seed 29 Feb 2020; the yearly lattice lands on 28 Feb, which
        //     is exactly where ChronoUnit.YEARS.between (0) and the naive rule (1) disagree.
        cases.add(freq("T46-YR-A", "YEARS_ARM",
                "YEARS arm, 29 Feb 2020 seed -- the packed/naive whole-YEARS separator",
                LocalDate.of(2020, 2, 29), LocalDate.of(2020, 2, 29), "1200000", 3, "21.6", "t46_yr_a",
                "YEARS", 1));
        cases.add(freq("T46-YR-B", "YEARS_ARM",
                "YEARS arm, ordinary 15 Mar seed -- no packed/naive disagreement anywhere",
                LocalDate.of(2024, 3, 15), LocalDate.of(2024, 3, 15), "1200000", 3, "21.6", "t46_yr_b",
                "YEARS", 1));

        // --- WEEKS arm (:1407).
        cases.add(freq("T46-WK-A", "WEEKS_ARM", "WEEKS arm, aligned start = disbursement",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6", "t46_wk_a",
                "WEEKS", 1));
        cases.add(freq("T46-WK-B", "WEEKS_ARM", "WEEKS arm, disbursement AFTER the schedule start",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6", "t46_wk_b",
                "WEEKS", 1));
        cases.add(freq("T46-WK-C", "WEEKS_ARM", "WEEKS arm, repaymentEvery = 2",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6", "t46_wk_c",
                "WEEKS", 2));

        // --- DAYS arm (:1408).
        cases.add(freq("T46-DY-A", "DAYS_ARM", "DAYS arm, aligned start = disbursement",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6", "t46_dy_a",
                "DAYS", 1));
        cases.add(freq("T46-DY-B", "DAYS_ARM", "DAYS arm, repaymentEvery = 10",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6", "t46_dy_b",
                "DAYS", 10));

        // --- MONTHS with repaymentEvery = 2 and 3.  T44 blind spot 3: "every capture pins
        //     RepaymentEvery = 1, and RepaymentEvery is the OTHER reading's whole content, so a
        //     port could hard-code the multiplier to periodRatio AND mishandle RepaymentEvery
        //     and still pass all 16."
        cases.add(freq("T46-RE-2", "REPAY_EVERY",
                "MONTHS, repaymentEvery = 2 -- separates periodRatio from RepaymentEvery upward",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), "1200000", 6, "21.6", "t46_re_2",
                "MONTHS", 2));
        cases.add(freq("T46-RE-3", "REPAY_EVERY",
                "MONTHS, repaymentEvery = 3, drift anchoring (start 28 Jan, disbursement 31 Jan)",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6", "t46_re_3",
                "MONTHS", 3));
        cases.add(freq("T46-RE-2ME", "REPAY_EVERY",
                "MONTHS, repaymentEvery = 2, 31 Jan seed -- month-end anchoring at every=2",
                LocalDate.of(2024, 1, 31), LocalDate.of(2024, 1, 31), "1200000", 6, "21.6", "t46_re_2me",
                "MONTHS", 2));
        return cases;
    }

    /**
     * NEGATIVE-TEST HOOKS.  Never set on a capture run; the recorded output proves it, because
     * every case echoes the precision, the mode and the tenant rounding ordinal it actually ran
     * with -- and, unlike T39, it echoes them OFF THE MathContext OBJECT handed to the callee.
     */
    static List<Case> applyNegativeTestOverrides(final List<Case> in) {
        final String ordinal = System.getProperty("t46.tenantRoundingModeOrdinal");
        final String precision = System.getProperty("t46.mathContextPrecision");
        final String threadedMode = System.getProperty("t46.mathContextRoundingMode");
        if (ordinal == null && precision == null && threadedMode == null) {
            return in;
        }
        final List<Case> out = new ArrayList<>();
        for (Case c : in) {
            out.add(new Case(c.id(), c.family(), c.purpose(), c.startDate(), c.disbursementDate(),
                    c.principal(), c.noRepayments(), c.annualRate(),
                    precision == null ? c.precision() : Integer.parseInt(precision),
                    threadedMode == null ? c.mode() : RoundingMode.valueOf(threadedMode),
                    c.currencyCode(), c.currencyDigits(), c.dim(), c.diy(), c.diyCustom(), c.downPaymentPct(),
                    c.installmentMultiplesOf(), c.fixedLength(), c.interestRecognitionOnDisbursementDate(),
                    c.allowPartialPeriodInterestCalculation(), c.allowFullTermForTranche(), c.tenantId(),
                    ordinal == null ? c.tenantRoundingMode() : Integer.parseInt(ordinal), c.tenantTimeZone(),
                    c.repaymentFrequencyType(), c.repaymentEvery()));
        }
        return out;
    }

    public static void main(String[] args) {
        final String set = System.getProperty("t46.set", "reemit");
        final List<Case> base = switch (set) {
            case "reemit" -> reemitCases();
            case "arms" -> armsCases();
            default -> throw new IllegalArgumentException("unknown -Dt46.set=" + set);
        };
        final List<Case> cases = applyNegativeTestOverrides(base);
        final String ordinalOverride = System.getProperty("t46.tenantRoundingModeOrdinal");
        final String precisionOverride = System.getProperty("t46.mathContextPrecision");
        final String threadedModeOverride = System.getProperty("t46.mathContextRoundingMode");

        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"task\": \"T46\",\n");
        sb.append("  \"harness\": \"CapturePeriodRatio2.java\",\n");
        sb.append("  \"set\": \"").append(set).append("\",\n");
        sb.append("  \"question\": \"").append("reemit".equals(set)
                ? "F39-2/F39-3: re-emit T39's sixteen cases with the THREADED MathContext echoed off the object"
                : "T44 blind spots 2 and 3: calculatePeriodRatio's YEARS/WEEKS/DAYS arms, and RepaymentEvery > 1")
                .append("\",\n");
        sb.append("  \"path\": \"A -- embeddable seam, in-process, no server, no database\",\n");
        sb.append("  \"fineractCommit\": \"426a23544e8426a38ae43ae404670a0a7e85b9eb\",\n");
        sb.append("  \"moneyHelperPrecisionConstant\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append("  \"javaVersion\": \"").append(System.getProperty("java.version")).append("\",\n");
        sb.append("  \"javaVmName\": \"").append(System.getProperty("java.vm.name")).append("\",\n");
        sb.append("  \"javaVmVersion\": \"").append(System.getProperty("java.vm.version")).append("\",\n");
        sb.append("  \"javaVendor\": \"").append(System.getProperty("java.vendor")).append("\",\n");
        sb.append("  \"jvmUserTimezone\": \"").append(System.getProperty("user.timezone")).append("\",\n");
        sb.append("  \"jvmFileEncoding\": \"").append(System.getProperty("file.encoding")).append("\",\n");
        sb.append("  \"negativeTestTenantRoundingModeOrdinalOverride\": ")
                .append(ordinalOverride == null ? "null" : "\"" + ordinalOverride + "\"").append(",\n");
        sb.append("  \"negativeTestMathContextPrecisionOverride\": ")
                .append(precisionOverride == null ? "null" : "\"" + precisionOverride + "\"").append(",\n");
        sb.append("  \"negativeTestMathContextRoundingModeOverride\": ")
                .append(threadedModeOverride == null ? "null" : "\"" + threadedModeOverride + "\"").append(",\n");
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
        ThreadLocalContextUtil
                .setTenant(new FineractPlatformTenant(1L, c.tenantId(), c.tenantId(), c.tenantTimeZone(), null));
        MoneyHelper.initializeTenantRoundingMode(c.tenantId(), c.tenantRoundingMode());
        // AMBIENT context.  On Path A this is NOT the arithmetic: MoneyHelper's MathContext is
        // reached only through the fallback overloads, and for a 2-dp currency it is provably
        // never read [T42 E1].  It is recorded as ambient and labelled as ambient.
        String ambientMathContext;
        try {
            ambientMathContext = String.valueOf(MoneyHelper.getMathContext());
        } catch (RuntimeException e) {
            ambientMathContext = e.getClass().getName() + ": " + e.getMessage();
        }

        // THREADED context.  This is the object handed to generate(); everything below is read
        // OFF THIS REFERENCE, never off the case record (T42 rule 2; T44 finding F39-3).
        final MathContext mc = new MathContext(c.precision(), c.mode());
        final EmbeddableProgressiveLoanScheduleGenerator generator = new EmbeddableProgressiveLoanScheduleGenerator();
        final CurrencyData currency = new CurrencyData(c.currencyCode(), c.currencyCode(), c.currencyDigits(),
                c.installmentMultiplesOf(), c.currencyCode(), c.currencyCode());

        final LoanRepaymentScheduleModelData config = new LoanRepaymentScheduleModelData(c.startDate(), currency,
                c.principal(), c.disbursementDate(), c.noRepayments(), c.repaymentEvery(), c.repaymentFrequencyType(),
                c.annualRate(), BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0, c.dim(), c.diy(),
                c.downPaymentPct(), c.installmentMultiplesOf(), c.fixedLength(),
                c.interestRecognitionOnDisbursementDate(), c.diyCustom(), InterestMethod.DECLINING_BALANCE,
                c.allowPartialPeriodInterestCalculation(), c.allowFullTermForTranche());

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"family\": \"").append(c.family()).append("\",\n");
        b.append("      \"purpose\": \"").append(c.purpose()).append("\",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"scheduleGenerationStartDate\": \"").append(c.startDate()).append("\",\n");
        b.append("        \"disbursementDate\": \"").append(c.disbursementDate()).append("\",\n");
        b.append("        \"disbursementAmount\": \"").append(c.principal().toPlainString()).append("\",\n");
        b.append("        \"numberOfRepayments\": ").append(c.noRepayments()).append(",\n");
        b.append("        \"repaymentEvery\": ").append(c.repaymentEvery()).append(",\n");
        b.append("        \"repaymentFrequencyType\": \"").append(c.repaymentFrequencyType()).append("\",\n");
        b.append("        \"annualNominalInterestRate\": \"").append(c.annualRate().toPlainString()).append("\",\n");
        b.append("        \"mathContextPrecision\": ").append(c.precision()).append(",\n");
        b.append("        \"mathContextRoundingMode\": \"").append(c.mode()).append("\",\n");
        // ---- T44 F39-3: the THREADED MathContext, read off the object handed to generate() ----
        b.append("        \"threadedMathContext\": \"").append(mc.toString()).append("\",\n");
        b.append("        \"threadedMathContextPrecision\": ").append(mc.getPrecision()).append(",\n");
        b.append("        \"threadedMathContextRoundingMode\": \"").append(mc.getRoundingMode()).append("\",\n");
        b.append("        \"wiring\": \"PATH_A -- this MathContext object is the argument of ")
                .append("EmbeddableProgressiveLoanScheduleGenerator.generate(mc, modelData), which forwards it to ")
                .append("ProgressiveLoanScheduleGenerator.generate(mc, modelData) [CapturePeriodRatio2.java, run()]\",\n");
        b.append("        \"tenantId\": \"").append(c.tenantId()).append("\",\n");
        b.append("        \"tenantTimeZone\": \"").append(c.tenantTimeZone()).append("\",\n");
        b.append("        \"tenantRoundingModeOrdinal\": ").append(c.tenantRoundingMode()).append(",\n");
        b.append("        \"ambientMoneyHelperMathContext\": \"").append(ambientMathContext).append("\",\n");
        b.append("        \"currencyCode\": \"").append(c.currencyCode()).append("\",\n");
        b.append("        \"currencyDecimalPlaces\": ").append(c.currencyDigits()).append(",\n");
        b.append("        \"currencyInMultiplesOf\": ").append(c.installmentMultiplesOf()).append(",\n");
        b.append("        \"daysInMonth\": \"").append(c.dim()).append("\",\n");
        b.append("        \"daysInYear\": \"").append(c.diy()).append("\",\n");
        b.append("        \"daysInYearCustomStrategy\": ")
                .append(c.diyCustom() == null ? "null" : "\"" + c.diyCustom() + "\"").append(",\n");
        b.append("        \"downPaymentEnabled\": ")
                .append(BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0).append(",\n");
        b.append("        \"downPaymentPercentage\": \"").append(c.downPaymentPct().toPlainString()).append("\",\n");
        b.append("        \"installmentAmountInMultiplesOf\": ").append(c.installmentMultiplesOf()).append(",\n");
        b.append("        \"fixedLength\": ").append(c.fixedLength()).append(",\n");
        b.append("        \"interestRecognitionOnDisbursementDate\": ")
                .append(c.interestRecognitionOnDisbursementDate()).append(",\n");
        b.append("        \"interestMethod\": \"DECLINING_BALANCE\",\n");
        b.append("        \"allowPartialPeriodInterestCalculation\": ")
                .append(c.allowPartialPeriodInterestCalculation()).append(",\n");
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
