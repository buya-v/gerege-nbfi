/*
 * Golden-vector capture harness, PASS 3h — gerege-nbfi Fineract→Go migration, Tier 0.
 *
 * PASS 3h IS PASS 3f's RIG WITH A NEW CASE LIST. Every precondition, attestation field, column and
 * emission rule is preserved byte-for-byte; only the case list differs, and NOT ONE check was
 * weakened. All FOUR of pass 3f's rig calibrations are carried over unchanged and TWO more are
 * added, chosen to sit on exactly the two axes this pass extends.
 *
 * WHY THIS PASS EXISTS — task T64. T59 found `applyFinalPeriodResidual` (a faithful port of
 * ProgressiveEMICalculator.java:1160-1219) is O(n^2) on near-interest-only shapes and correctly
 * declined to fix it, because NO VECTOR GRADES THAT SHAPE. Measured: across all 32 promoted parity
 * vectors the longest term is n=36 and the smallest principal is MNT 100.00, and not one contains a
 * REPAYMENT row whose principal is 0.
 *
 * DERIVED FROM SOURCE, NOT SEARCHED FOR. A repayment row's principal is max(0, EMI - dueInterest)
 * [RepaymentPeriod.java:345-350], both quantized to the currency scale [Money.java:52], and the
 * exact EMI/interest gap is B*r/((1+r)^n - 1) > 0 for every finite n. So the two can only quantize
 * to the same minor unit at the ROUNDING FLOOR:
 *
 *     B >= ceil(0.5/r)   so period-1 interest quantizes to at least 1 minor unit, and
 *     n >  2*B           so the EMI smoothing adjustment B/n quantizes to zero and the loop breaks
 *                        [ProgressiveEMICalculator.java:1270-1273; uncountablePeriods is 0 at
 *                        origination, :2027-2031]
 *
 * with B the principal in MINOR UNITS. The full derivation, the ten-rate check of the bound and the
 * cell-for-cell prediction live in .softhouse/capture/t64-zeroprincipal/PREDICTION.md and
 * predicted-schedules.json, and were committed BEFORE this harness was written.
 *
 * SIX CALIBRATIONS AND FOUR PARITY CANDIDATES:
 *
 *   P-CAL          RIG CALIBRATION at (12, HALF_UP), inputs identical to pass 3b's P-CAL.
 *   P-CAL-P00      RIG CALIBRATION at PRODUCTION (19, HALF_UP), inputs identical to pass 3b's P-00.
 *   P-CAL-EMI6     RIG CALIBRATION in MNT, inputs identical to pass 3c's P-EMI-6-1M014632.
 *   P-CAL-LATQ0a   RIG CALIBRATION in MNT, inputs identical to pass 3e's P-LAT-Q0a.
 *   P-CAL-MNT50M   RIG CALIBRATION ADDED BY PASS 3h: inputs identical to pass 3b's P-MNT-50M, the
 *                  LONGEST TERM in the promoted corpus (n=36). This pass's candidates run at n=34
 *                  to n=72, so the rig is calibrated at the far end of the term axis it extends.
 *   P-CAL-DRIFTF   RIG CALIBRATION ADDED BY PASS 3h: inputs identical to pass 3e's P-DRIFT-F, the
 *                  SMALLEST PRINCIPAL in the promoted corpus (MNT 1.00). This pass's candidates run
 *                  at MNT 0.17 to MNT 0.36, so the rig is calibrated at the far end of the
 *                  principal axis it extends too.
 *   T64-ZP-A/B/C/D four parity candidates. All four are ordinary single-disbursement MNT loans
 *                  strictly inside DEC-1's graded domain: disbursement ON the schedule start date,
 *                  RepaymentEvery 1 MONTHS, DECLINING_BALANCE, DAYS_30/DAYS_360, no down payment,
 *                  no installment rounding, MNT 2 decimals, (19, HALF_UP). Only the principal, the
 *                  term and the rate move.
 *
 * None of the six calibrations is a parity vector and P-CAL is on PIN.json's never-promotable list.
 *
 * It asserts nothing and predicts nothing — every value printed is what the oracle emitted. In
 * particular this harness does NOT know which rows it expects to be zero, does NOT count them and
 * does NOT decide whether a shape is at the rounding floor: it prints the oracle's schedule and
 * stops.
 *
 * PRODUCTION SETTINGS. Buyan ratified the tenant parameters on 2026-08-18: rounding mode HALF_UP,
 * licence NBFI. Precision is not a choice — MoneyHelper.PRECISION = 19 is a compile-time constant and
 * getMathContext() returns new MathContext(19, tenantRoundingMode) [MoneyHelper.java:35, 91-93]. So the
 * PRODUCTION MathContext is (19, HALF_UP).
 *
 * PostgreSQL remains the only permitted database for this program; this seam opens no database
 * connection at all. "The oracle" here is the Fineract reference implementation, never Oracle
 * Database (a prohibited product).
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
import org.apache.fineract.portfolio.loanaccount.domain.Loan;
import org.apache.fineract.portfolio.loanaccount.domain.ProgressiveLoanModel;
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

import java.io.File;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.util.Optional;
import java.io.IOException;
import java.io.InputStream;
import java.lang.management.ManagementFactory;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.TimeZone;

public class Capture3h {

    /**
     * One capture run. Identical record to Capture3.java's Case — do not change it; the pass-3
     * comparison depends on the inputs being the same values.
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

    /**
     * Production settings with an EXPLICIT schedule-start and disbursement date, which may differ.
     * Every other field is C-00's, exactly as {@link #prod} leaves them; only the two dates move.
     * This is the ONLY structural addition pass 3e makes to pass 3d's harness.
     */
    static Case prodDates(String id, String purpose, LocalDate startDate, LocalDate disbursementDate,
            BigDecimal principal, int noRepayments, BigDecimal rate, String tenantId) {
        return new Case(id, purpose, startDate, disbursementDate, principal, noRepayments, rate, 19,
                RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, false, true, false, tenantId, 4);
    }

    public static void main(String[] args) throws Exception {
        final List<Case> cases = new ArrayList<>();

        // ---- RIG CALIBRATIONS — reproduce values ALREADY OBSERVED in the committed corpus ------
        // Inputs below are byte-identical to the passes they repeat, TENANT ID INCLUDED, so the
        // whole observed block of each must equal the committed entry of the same shape. If any
        // one differs, nothing else from this run is trustworthy and run-pass3f.sh refuses it.
        cases.add(prod("P-CAL", "RIG CALIBRATION at (12, HALF_UP) — inputs identical to pass 3b P-CAL; must reproduce it digit for digit; NOT a parity vector",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, false, "usd", "cap_p_cal"));

        cases.add(prod("P-CAL-P00", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) — inputs identical to pass 3b P-00; must reproduce it digit for digit at the precision the parity candidates run at; NOT a parity vector",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19, null, false, "usd", "cap_p_00"));

        cases.add(prod("P-CAL-EMI6", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3c P-EMI-6-1M014632; must reproduce it digit for digit; NOT a parity vector",
                new BigDecimal("1014632"), 6, new BigDecimal("7.0"), 19, null, false, "MNT", "cap_p_emi_6"));

        // ---- FOURTH CALIBRATION, ADDED BY PASS 3f ------------------------------------------------
        // Inputs byte-identical to pass 3e's P-LAT-Q0a, tenant id included. That case is ALREADY a
        // promoted parity vector, and it is the SAME QUESTION as the three candidates below in
        // every field but the principal: same lattice date, same term, same rate, same currency,
        // same MathContext. A rig that reproduces it is calibrated on exactly the arithmetic the
        // promotion rests on, not merely on something nearby.
        cases.add(prodDates("P-CAL-LATQ0a", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3e P-LAT-Q0a, the on-lattice control the three candidates differ from ONLY in principal; must reproduce it digit for digit; NOT a parity vector",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("1200000"), 6, new BigDecimal("21.6"), "cap_lat_q0a"));

        // ---- CALIBRATIONS ADDED BY PASS 3h -------------------------------------------------
        // Inputs byte-identical to the committed captures they repeat, tenant id included. They are
        // chosen for the AXES this pass extends: P-MNT-50M is the longest term in the promoted
        // corpus (n=36) and P-DRIFT-F is the smallest principal in it (MNT 1.00). The candidates
        // below run longer than the first and smaller than the second, so the rig is calibrated at
        // the far end of both axes rather than merely somewhere nearby.
        cases.add(prod("P-CAL-MNT50M", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3b P-MNT-50M, the LONGEST TERM in the promoted corpus; must reproduce it digit for digit; NOT a parity vector",
                new BigDecimal("50000000"), 36, new BigDecimal("16.8"), 19, null, false, "MNT", "cap_p_mnt50m"));

        cases.add(prodDates("P-CAL-DRIFTF", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3e P-DRIFT-F, the SMALLEST PRINCIPAL in the promoted corpus; must reproduce it digit for digit; NOT a parity vector",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), new BigDecimal("100"), 6, new BigDecimal("21.6"), "cap_drift_f"));

        // ---- PARITY CANDIDATES — four MNT loans at the ROUNDING FLOOR ----------------------
        // Strictly inside the graded domain: single disbursement ON the schedule start date,
        // RepaymentEvery 1 MONTHS, DECLINING_BALANCE, DAYS_30/DAYS_360, no down payment, no
        // installment rounding, MNT 2 decimals, (19, HALF_UP). Only principal, term and rate move.
        //
        // ---- TWO MORE CALIBRATIONS, ADDED BY PASS 3h ------------------------------------------
        // Inputs byte-identical to pass 3g's T64-ZP-A and T64-ZP-B, tenant id included. BOTH are
        // ALREADY promoted parity vectors. ZP-B is the ONLY shape in the entire committed corpus
        // whose schedule carries a ZERO-EMI TAIL (installments 16..55 all zero), which is exactly
        // the precondition half that T63 could not test, so this pass calibrates ON the shape it
        // interrogates rather than merely near it.
        cases.add(prodDates("P-CAL-ZPA", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3g T64-ZP-A, an already-promoted parity vector at the rounding floor; must reproduce it digit for digit; NOT a parity vector",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 56, new BigDecimal("21.6"), "cap_t64_zp_a"));

        cases.add(prodDates("P-CAL-ZPB", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3g T64-ZP-B, an already-promoted parity vector and the ONLY committed shape with a ZERO-EMI TAIL; must reproduce it digit for digit; NOT a parity vector",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 55, new BigDecimal("21.6"), "cap_t64_zp_b"));

        // ---- MECHANISM PROBES — task T66 -------------------------------------------------------
        // Every case in this pass emits the mechanism columns; these ten exist to push the
        // futureUnrecognizedInterest precondition as hard as DEC-1's graded domain allows. The
        // graded domain fixes single disbursement / 1 MONTHS / DECLINING_BALANCE / DAYS_30 /
        // DAYS_360 / no down payment / no installment rounding / MNT 2 decimals / (19, HALF_UP);
        // it places NO upper bound on the nominal rate and none on the term, and those are the two
        // axes the precondition is sensitive to. At 30/360 monthly the first period's rate factor
        // is annualRate/12, so 1200% is r = 1.00 exactly and 12000% is r = 10.00.
        //
        // This harness asserts nothing and predicts nothing. The falsifiable prediction registered
        // for these cases lives in .softhouse/capture/t66-unrecognized-interest/PREDICTION.md and
        // was committed BEFORE this file was written.
        cases.add(prodDates("T66-M-R1200", "MECHANISM PROBE: MNT 12,000.00 / 6 x 1200% — first-period rate factor exactly 1.00, the boundary of the sufficient condition in the T66 proof",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("12000"), 6, new BigDecimal("1200"), "cap_t66_r1200"));

        cases.add(prodDates("T66-M-R2400", "MECHANISM PROBE: MNT 12,000.00 / 6 x 2400% — first-period rate factor 2.00, STRICTLY ABOVE the proof's sufficient condition",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("12000"), 6, new BigDecimal("2400"), "cap_t66_r2400"));

        cases.add(prodDates("T66-M-R2400-LONG", "MECHANISM PROBE: MNT 12,000.00 / 60 x 2400% — same rate factor, ten times the term, so a long tail of near-interest-only periods exists to carry unrecognized interest into",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("12000"), 60, new BigDecimal("2400"), "cap_t66_r2400_long"));

        cases.add(prodDates("T66-M-R12000", "MECHANISM PROBE: MNT 12,000.00 / 12 x 12000% — first-period rate factor 10.00, an order of magnitude past the proof's sufficient condition",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("12000"), 12, new BigDecimal("12000"), "cap_t66_r12000"));

        cases.add(prodDates("T66-M-DRIFT-R2400", "MECHANISM PROBE: start 2024-01-28, disbursed 2024-01-31, MNT 12,000.00 / 6 x 2400% — the month-end re-anchor drift region, so the periodRatio (and hence the per-period rate factor) is NOT uniform, combined with a rate factor of 2.00",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), new BigDecimal("12000"), 6, new BigDecimal("2400"), "cap_t66_drift_r2400"));

        cases.add(prodDates("T66-M-DRIFT-R12000", "MECHANISM PROBE: start 2024-01-28, disbursed 2024-01-31, MNT 12,000.00 / 12 x 12000% — drift region at rate factor 10.00",
                LocalDate.of(2024, 1, 28), LocalDate.of(2024, 1, 31), new BigDecimal("12000"), 12, new BigDecimal("12000"), "cap_t66_drift_r12000"));

        cases.add(prodDates("T66-M-DISB-ON-DUE", "MECHANISM PROBE: MNT 1,200,000.00 / 6 x 21.6%, disbursed ON the first repayment due date 2024-02-01 — the only admitted shape in which tillDate is NOT the first period's due date, so the index f of the tillDate period is 1 and period 0 lies OUTSIDE the related window",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 2, 1), new BigDecimal("1200000"), 6, new BigDecimal("21.6"), "cap_t66_disb_on_due"));

        cases.add(prodDates("T66-M-DISB-ON-DUE-HR", "MECHANISM PROBE: the same f=1 shape at 2400% — MNT 12,000.00 / 6, disbursed ON the first repayment due date",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 2, 1), new BigDecimal("12000"), 6, new BigDecimal("2400"), "cap_t66_disb_on_due_hr"));

        cases.add(prodDates("T66-M-FLOOR-HR", "MECHANISM PROBE: MNT 0.03 / 5 x 2400% — the rounding floor at a rate factor of 2.00, where the installment and the first period's interest quantize to the same minor unit",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.03"), 5, new BigDecimal("2400"), "cap_t66_floor_hr"));

        cases.add(prodDates("T66-M-FLOOR-LONG", "MECHANISM PROBE: MNT 0.28 / 120 x 21.6% — the ZP-B family with more than twice the term, so the zero-EMI tail is longer than any in the committed corpus",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 120, new BigDecimal("21.6"), "cap_t66_floor_long"));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"pass\": \"3h\",\n");
        sb.append("  \"harness\": \"Capture3h.java\",\n");
        sb.append("  \"extends\": \"Capture3g.java / capture-prod3g-raw.json — same rig, same columns, same attestation, same emission rules, ALL SIX of pass 3g's calibrations carried over unchanged plus TWO more taken from pass 3g's own promoted output (P-CAL-ZPA and P-CAL-ZPB, inputs identical to T64-ZP-A and T64-ZP-B; ZP-B is the ONLY shape in the whole committed corpus carrying a ZERO-EMI TAIL, which is exactly the shape this pass exists to interrogate). Pass 3h ADDS ONE COLUMN FAMILY the earlier passes could not record: the per-period MECHANISM columns futureUnrecognizedInterest, interestMovedUpward, calculatedDueInterest, dueInterest, unrecognizedInterest, emi, isFullyPaid, read straight off the ProgressiveLoanInterestScheduleModel the oracle's own ProgressiveLoanScheduleGenerator built. It does NOT modify the seam class and does NOT reimplement the algorithm: it constructs the oracle's OWN ProgressiveLoanScheduleGenerator with the oracle's OWN ProgressiveEMICalculator behind a java.lang.reflect.Proxy that only records the model reference and delegates every call unchanged. Every case is ALSO run through the pristine embeddable seam and the two schedules are emitted side by side, so the runner can fail the run if the instrumented path is not the same computation (PATH IDENTITY calibration).\",\n");
        sb.append("  \"moneyHelperPrecision\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append(attestation());
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

    // ---------------------------------------------------------------------------------------
    // ATTESTATION — T21 P0-2. Everything outside "runnerSupplied" is read inside this JVM, in this
    // container, during this run. Everything inside "runnerSupplied" is an echo of an environment
    // variable the runner script set; it is labelled as an echo and is NOT a measurement.
    // ---------------------------------------------------------------------------------------
    static String attestation() throws Exception {
        StringBuilder a = new StringBuilder();
        a.append("  \"attestation\": {\n");
        a.append("    \"capturePath\": \"Path A — embeddable progressive-loan schedule-generator seam, in-process. No Fineract server is started and no database connection is opened.\",\n");
        a.append("    \"capturedAtUtc\": \"").append(Instant.now().toString()).append("\",\n");

        // --- the oracle's own identity, from the jar the classpath was built out of ---
        Properties git = new Properties();
        try (InputStream in = Capture3h.class.getResourceAsStream("/git.properties")) {
            if (in != null) {
                git.load(in);
            }
        }
        String jarPath = System.getenv("ATTEST_JAR_PATH") == null ? "/app/fineract-provider.jar"
                : System.getenv("ATTEST_JAR_PATH");
        File jar = new File(jarPath);
        a.append("    \"fineract\": {\n");
        a.append("      \"gitPropertiesSource\": \"BOOT-INF/classes/git.properties inside ").append(esc(jarPath)).append("\",\n");
        a.append("      \"gitCommitId\": ").append(q(git.getProperty("git.commit.id"))).append(",\n");
        a.append("      \"gitCommitIdDescribe\": ").append(q(git.getProperty("git.commit.id.describe"))).append(",\n");
        a.append("      \"gitCommitTime\": ").append(q(git.getProperty("git.commit.time"))).append(",\n");
        a.append("      \"gitBranch\": ").append(q(git.getProperty("git.branch"))).append(",\n");
        a.append("      \"gitDirty\": ").append(q(git.getProperty("git.dirty"))).append(",\n");
        a.append("      \"gitBuildVersion\": ").append(q(git.getProperty("git.build.version"))).append(",\n");
        a.append("      \"providerJarPath\": ").append(q(jarPath)).append(",\n");
        a.append("      \"providerJarSizeBytes\": ").append(jar.isFile() ? String.valueOf(jar.length()) : "null").append(",\n");
        a.append("      \"providerJarSha256\": ").append(q(jar.isFile() ? sha256File(jar.toPath()) : null)).append("\n");
        a.append("    },\n");

        // --- JVM identity and flags ---
        a.append("    \"jvm\": {\n");
        a.append("      \"javaVersion\": ").append(q(System.getProperty("java.version"))).append(",\n");
        a.append("      \"javaRuntimeVersion\": ").append(q(System.getProperty("java.runtime.version"))).append(",\n");
        a.append("      \"javaVmName\": ").append(q(System.getProperty("java.vm.name"))).append(",\n");
        a.append("      \"javaVmVersion\": ").append(q(System.getProperty("java.vm.version"))).append(",\n");
        a.append("      \"javaVendor\": ").append(q(System.getProperty("java.vendor"))).append(",\n");
        a.append("      \"javaHome\": ").append(q(System.getProperty("java.home"))).append(",\n");
        a.append("      \"osName\": ").append(q(System.getProperty("os.name"))).append(",\n");
        a.append("      \"osVersion\": ").append(q(System.getProperty("os.version"))).append(",\n");
        a.append("      \"osArch\": ").append(q(System.getProperty("os.arch"))).append(",\n");
        a.append("      \"fileEncoding\": ").append(q(System.getProperty("file.encoding"))).append(",\n");
        a.append("      \"defaultLocale\": ").append(q(java.util.Locale.getDefault().toString())).append(",\n");
        a.append("      \"defaultTimeZone\": ").append(q(TimeZone.getDefault().getID())).append(",\n");
        a.append("      \"userTimezoneProperty\": ").append(q(System.getProperty("user.timezone"))).append(",\n");
        List<String> flags = ManagementFactory.getRuntimeMXBean().getInputArguments();
        a.append("      \"inputArguments\": [");
        for (int i = 0; i < flags.size(); i++) {
            a.append(i == 0 ? "" : ", ").append(q(flags.get(i)));
        }
        a.append("],\n");
        a.append("      \"inputArgumentCount\": ").append(flags.size()).append("\n");
        a.append("    },\n");

        // --- the rounding seam, as it actually is in this JVM ---
        // Probed under a tenant of its own so no capture tenant is disturbed.
        String probeTenant = "attest_probe";
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, probeTenant, probeTenant, "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(probeTenant, 4);
        MathContext probeMc = MoneyHelper.getMathContext();
        RoundingMode probeRm = MoneyHelper.getRoundingMode();
        a.append("    \"moneyHelper\": {\n");
        a.append("      \"precisionCompileTimeConstant\": ").append(MoneyHelper.PRECISION).append(",\n");
        a.append("      \"probeTenantId\": ").append(q(probeTenant)).append(",\n");
        a.append("      \"probeTenantRoundingModeValueRequested\": 4,\n");
        a.append("      \"effectiveMathContextPrecision\": ").append(probeMc.getPrecision()).append(",\n");
        a.append("      \"effectiveMathContextRoundingMode\": ").append(q(probeMc.getRoundingMode().name())).append(",\n");
        a.append("      \"effectiveMathContextRoundingModeOrdinal\": ").append(probeMc.getRoundingMode().ordinal()).append(",\n");
        a.append("      \"effectiveRoundingMode\": ").append(q(probeRm.name())).append(",\n");
        a.append("      \"effectiveRoundingModeOrdinal\": ").append(probeRm.ordinal()).append(",\n");
        a.append("      \"effectiveMathContextToString\": ").append(q(probeMc.toString())).append(",\n");
        a.append("      \"ratifiedProductionSetting\": \"(19, HALF_UP) — RoundingMode.HALF_UP ordinal 4\",\n");
        a.append("      \"matchesRatifiedProductionSetting\": ")
                .append(probeMc.getPrecision() == 19 && probeRm == RoundingMode.HALF_UP).append("\n");
        a.append("    },\n");
        ThreadLocalContextUtil.reset();

        // --- what was compiled, and what it was compiled against ---
        String srcList = System.getenv("ATTEST_SOURCES") == null
                ? "/cap/src/Capture3h.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java"
                : System.getenv("ATTEST_SOURCES");
        a.append("    \"sources\": [");
        String[] srcs = srcList.split(":");
        for (int i = 0; i < srcs.length; i++) {
            Path p = Paths.get(srcs[i]);
            a.append(i == 0 ? "\n" : ",\n");
            a.append("      {\"file\": ").append(q(srcs[i])).append(", \"sha256\": ")
                    .append(q(Files.isRegularFile(p) ? sha256File(p) : null)).append("}");
        }
        a.append("\n    ],\n");

        String[] cp = System.getProperty("java.class.path").split(File.pathSeparator);
        List<String> lines = new ArrayList<>();
        for (String entry : cp) {
            Path p = Paths.get(entry);
            String d = Files.isRegularFile(p) ? sha256File(p) : "DIRECTORY_OR_MISSING";
            lines.add(d + "  " + entry);
        }
        List<String> sorted = new ArrayList<>(lines);
        java.util.Collections.sort(sorted);
        String aggregate = sha256Bytes(String.join("\n", sorted).getBytes(StandardCharsets.UTF_8));
        String cpOut = System.getenv("ATTEST_CLASSPATH_OUT") == null
                ? "/cap/out/capture-prod3h-classpath-sha256.txt" : System.getenv("ATTEST_CLASSPATH_OUT");
        try {
            Files.write(Paths.get(cpOut), (String.join("\n", sorted) + "\n").getBytes(StandardCharsets.UTF_8));
        } catch (IOException e) {
            // recorded, never silently swallowed
            cpOut = "WRITE_FAILED: " + e.getClass().getName() + ": " + e.getMessage();
        }
        a.append("    \"classpath\": {\n");
        a.append("      \"entryCount\": ").append(cp.length).append(",\n");
        a.append("      \"aggregateSha256\": ").append(q(aggregate)).append(",\n");
        a.append("      \"aggregateSha256Definition\": \"sha256 over the newline-joined, lexicographically sorted list of '<sha256>  <classpath entry>' lines\",\n");
        a.append("      \"perEntryDigestFile\": ").append(q(cpOut)).append("\n");
        a.append("    },\n");

        // --- echoes, explicitly not measurements ---
        a.append("    \"runnerSupplied\": {\n");
        a.append("      \"NOTE\": \"ECHOED from the runner's environment. NOT measured inside the container — the container cannot read the docker image id or the host checkout. The runner script asserts these independently and fails the run on mismatch.\",\n");
        a.append("      \"dockerImageRef\": ").append(q(System.getenv("ATTEST_IMAGE_REF"))).append(",\n");
        a.append("      \"dockerImageId\": ").append(q(System.getenv("ATTEST_IMAGE_ID"))).append(",\n");
        a.append("      \"pinnedFineractCommit\": ").append(q(System.getenv("ATTEST_PINNED_COMMIT"))).append(",\n");
        a.append("      \"pinnedFineractPath\": ").append(q(System.getenv("ATTEST_PINNED_PATH"))).append(",\n");
        a.append("      \"runId\": ").append(q(System.getenv("ATTEST_RUN_ID"))).append("\n");
        a.append("    }\n");
        a.append("  },\n");
        return a.toString();
    }

    static String sha256File(Path p) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        try (InputStream in = Files.newInputStream(p)) {
            byte[] buf = new byte[65536];
            int n;
            while ((n = in.read(buf)) > 0) {
                md.update(buf, 0, n);
            }
        }
        return hex(md.digest());
    }

    static String sha256Bytes(byte[] b) throws Exception {
        return hex(MessageDigest.getInstance("SHA-256").digest(b));
    }

    static String hex(byte[] b) {
        StringBuilder s = new StringBuilder();
        for (byte x : b) {
            s.append(String.format("%02x", x));
        }
        return s.toString();
    }

    static String esc(String s) {
        return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", " ").replace("\r", " ").replace("\t", " ");
    }

    /** JSON string literal, or the bare token null. */
    static String q(String s) {
        return s == null ? "null" : "\"" + esc(s) + "\"";
    }

    /** Every BigDecimal leaves this harness through here — T21 P1-9, toPlainString(). */
    static String pl(BigDecimal d) {
        return d == null ? "null" : d.toPlainString();
    }

    static String run(final Case c) {
        // Establish (or deliberately withhold) the tenant context for THIS case only.
        String ambientMathContext;
        String ambientPrecision;
        String ambientRoundingMode;
        String ambientRoundingModeOrdinal;
        if (c.tenantId() == null) {
            ThreadLocalContextUtil.reset();
            ambientMathContext = "null (no tenant context)";
            ambientPrecision = "null";
            ambientRoundingMode = "null";
            ambientRoundingModeOrdinal = "null";
        } else {
            ThreadLocalContextUtil.setTenant(
                    new FineractPlatformTenant(1L, c.tenantId(), c.tenantId(), "Asia/Ulaanbaatar", null));
            MoneyHelper.initializeTenantRoundingMode(c.tenantId(), c.tenantRoundingMode());
            try {
                MathContext ambient = MoneyHelper.getMathContext();
                ambientMathContext = String.valueOf(ambient);
                ambientPrecision = String.valueOf(ambient.getPrecision());
                ambientRoundingMode = "\"" + ambient.getRoundingMode().name() + "\"";
                ambientRoundingModeOrdinal = String.valueOf(ambient.getRoundingMode().ordinal());
            } catch (RuntimeException e) {
                ambientMathContext = e.getClass().getName() + ": " + e.getMessage();
                ambientPrecision = "null";
                ambientRoundingMode = "null";
                ambientRoundingModeOrdinal = "null";
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
        b.append("        \"disbursementAmount\": \"").append(pl(c.principal())).append("\",\n");
        b.append("        \"numberOfRepayments\": ").append(c.noRepayments()).append(",\n");
        b.append("        \"repaymentFrequency\": 1,\n");
        b.append("        \"repaymentFrequencyType\": \"MONTHS\",\n");
        b.append("        \"annualNominalInterestRate\": \"").append(pl(c.annualRate())).append("\",\n");
        b.append("        \"mathContextPrecision\": ").append(c.precision()).append(",\n");
        b.append("        \"mathContextRoundingMode\": \"").append(c.mode()).append("\",\n");
        b.append("        \"mathContextRoundingModeOrdinal\": ").append(c.mode().ordinal()).append(",\n");
        b.append("        \"tenantId\": ").append(c.tenantId() == null ? "null" : "\"" + c.tenantId() + "\"").append(",\n");
        b.append("        \"tenantRoundingModeValue\": ").append(c.tenantRoundingMode()).append(",\n");
        b.append("        \"ambientMoneyHelperMathContext\": \"").append(ambientMathContext).append("\",\n");
        b.append("        \"ambientMoneyHelperPrecision\": ").append(ambientPrecision).append(",\n");
        b.append("        \"ambientMoneyHelperRoundingMode\": ").append(ambientRoundingMode).append(",\n");
        b.append("        \"ambientMoneyHelperRoundingModeOrdinal\": ").append(ambientRoundingModeOrdinal).append(",\n");
        b.append("        \"currencyCode\": \"").append(c.currencyCode()).append("\",\n");
        b.append("        \"currencyDecimalPlaces\": ").append(c.currencyDigits()).append(",\n");
        b.append("        \"currencyInMultiplesOf\": ").append(c.installmentMultiplesOf()).append(",\n");
        b.append("        \"daysInMonth\": \"").append(c.dim()).append("\",\n");
        b.append("        \"daysInYear\": \"").append(c.diy()).append("\",\n");
        b.append("        \"daysInYearCustomStrategy\": ").append(c.diyCustom() == null ? "null" : "\"" + c.diyCustom() + "\"").append(",\n");
        b.append("        \"downPaymentEnabled\": ").append(BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0).append(",\n");
        b.append("        \"downPaymentPercentage\": \"").append(pl(c.downPaymentPct())).append("\",\n");
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
            // T21 P1-9: keep the frames. A discarded stack trace is a lost finding.
            b.append("      \"observed\": null,\n");
            b.append("      \"error\": \"").append(e.getClass().getName()).append(": ")
                    .append(String.valueOf(e.getMessage()).replace("\"", "'").replace("\n", " ")).append("\",\n");
            b.append("      \"errorStackTop\": [");
            StackTraceElement[] st = e.getStackTrace();
            int n = Math.min(st.length, 25);
            for (int i = 0; i < n; i++) {
                b.append(i == 0 ? "" : ", ").append(q(st[i].toString()));
            }
            b.append("],\n");
            Throwable cause = e.getCause();
            b.append("      \"errorCause\": ").append(q(cause == null ? null : cause.getClass().getName() + ": " + cause.getMessage())).append("\n");
            b.append("    }");
            e.printStackTrace(System.err);
            return b.toString();
        }

        b.append("      \"observed\": {\n");
        b.append("        \"loanTermInDays\": ").append(plan.getLoanTermInDays()).append(",\n");
        b.append("        \"totalDisbursedAmount\": \"").append(pl(plan.getTotalDisbursedAmount())).append("\",\n");
        b.append("        \"totalPrincipalAmount\": \"").append(pl(plan.getTotalPrincipalAmount())).append("\",\n");
        b.append("        \"totalInterestAmount\": \"").append(pl(plan.getTotalInterestAmount())).append("\",\n");
        b.append("        \"totalFeeAmount\": \"").append(pl(plan.getTotalFeeAmount())).append("\",\n");
        b.append("        \"totalPenaltyAmount\": \"").append(pl(plan.getTotalPenaltyAmount())).append("\",\n");
        b.append("        \"totalRepaymentAmount\": \"").append(pl(plan.getTotalRepaymentAmount())).append("\",\n");
        b.append("        \"totalOutstandingAmount\": \"").append(pl(plan.getTotalOutstandingAmount())).append("\",\n");
        b.append("        \"periods\": [\n");

        final List<String> rows = new ArrayList<>();
        for (LoanSchedulePlanPeriod period : plan.getPeriods()) {
            if (period instanceof LoanSchedulePlanDisbursementPeriod dp) {
                rows.add("          {\"type\": \"DISBURSEMENT\", \"periodFromDate\": \"" + dp.periodFromDate()
                        + "\", \"dueDate\": \"" + dp.periodDueDate()
                        + "\", \"principal\": \"" + pl(dp.getPrincipalAmount())
                        + "\", \"balance\": \"" + pl(dp.getOutstandingLoanBalance()) + "\"}");
            } else if (period instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                rows.add("          {\"type\": \"DOWN_PAYMENT\", \"periodNumber\": " + dpp.periodNumber()
                        + ", \"periodFromDate\": \"" + dpp.periodFromDate()
                        + "\", \"dueDate\": \"" + dpp.periodDueDate() + "\", \"balance\": \""
                        + pl(dpp.getOutstandingLoanBalance()) + "\", \"principal\": \"" + pl(dpp.getPrincipalAmount())
                        + "\", \"total\": \"" + pl(dpp.getTotalDueAmount()) + "\", \"totalOutstandingBalance\": \""
                        + pl(dpp.getTotalOutstandingLoanBalance()) + "\"}");
            } else if (period instanceof LoanSchedulePlanRepaymentPeriod rp) {
                rows.add("          {\"type\": \"REPAYMENT\", \"periodNumber\": " + rp.periodNumber()
                        + ", \"periodFromDate\": \"" + rp.periodFromDate()
                        + "\", \"dueDate\": \"" + rp.periodDueDate() + "\", \"balance\": \""
                        + pl(rp.getOutstandingLoanBalance()) + "\", \"principal\": \"" + pl(rp.getPrincipalAmount())
                        + "\", \"interest\": \"" + pl(rp.getInterestAmount())
                        + "\", \"feeAmount\": \"" + pl(rp.getFeeAmount())
                        + "\", \"penaltyAmount\": \"" + pl(rp.getPenaltyAmount())
                        + "\", \"total\": \"" + pl(rp.getTotalDueAmount()) + "\", \"totalOutstandingBalance\": \""
                        + pl(rp.getTotalOutstandingLoanBalance()) + "\"}");
            } else {
                rows.add("          {\"type\": \"UNKNOWN:" + period.getClass().getName() + "\"}");
            }
        }
        b.append(String.join(",\n", rows)).append("\n");
        b.append("        ]\n");
        b.append("      },\n");

        // ---- MECHANISM COLUMNS + PATH IDENTITY, added by pass 3h -----------------------------
        b.append(mechanism(mc, config, plan));

        b.append("    }");
        return b.toString();
    }

    // ---------------------------------------------------------------------------------------
    // THE MECHANISM PROBE — task T66.
    //
    // It does NOT modify the seam class and does NOT reimplement anything. It builds the
    // oracle's OWN ProgressiveLoanScheduleGenerator around the oracle's OWN
    // ProgressiveEMICalculator (which is `final`, so a subclass is impossible) placed behind a
    // java.lang.reflect.Proxy whose entire behaviour is: delegate the call unchanged, and if the
    // method was generatePeriodInterestScheduleModel, remember the returned model reference. The
    // model the generator then mutates is that same object, so after generate() returns, the
    // per-period fields below are the oracle's own final state.
    //
    // WHAT IS OBSERVED, and why each field is here:
    //   futureUnrecognizedInterest  the field the port does not have. It is written ONLY at
    //                               ProgressiveEMICalculator.java:1250 and reset to zero at :1183
    //                               on entry to calculateLastUnpaidRepaymentPeriodEMI, and on the
    //                               ordinary generate path that method is entered on the real
    //                               model exactly once (:747). Nothing after :747 resets it on the
    //                               real model — :1288's calls run on the smoothing loop's trial
    //                               copy — so this final value IS the outcome of the one decision.
    //   interestMovedUpward         written true at :1249 on every period after the target, reset
    //                               false at :1185. Same argument.
    //   unrecognizedInterest        negativeToZero(calculatedDueInterest - dueInterest)
    //                               [RepaymentPeriod.java:381-383] — the quantity
    //                               getPeriodWithUnrecognizedInterest tests (:1806-1808).
    //   calculatedDueInterest/dueInterest/emi/isFullyPaid/totalPaidAmount
    //                               the inputs to that quantity, so a reader can re-derive it.
    //
    // PATH IDENTITY. The plan the instrumented generator returns is emitted alongside the
    // pristine seam's plan, cell for cell, and the runner FAILS THE RUN if they differ. That is
    // what makes the mechanism columns evidence about the seam's computation rather than about a
    // lookalike.
    // ---------------------------------------------------------------------------------------
    static String mechanism(final MathContext mc, final LoanRepaymentScheduleModelData config,
            final LoanSchedulePlan seamPlan) {
        final StringBuilder b = new StringBuilder();
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

        final LoanSchedulePlan probePlan;
        try {
            probePlan = new ProgressiveLoanScheduleGenerator(sdg, spy, new NoopModelRepositoryWrapper())
                    .generate(mc, config);
        } catch (RuntimeException e) {
            b.append("      \"mechanism\": null,\n");
            b.append("      \"mechanismError\": ").append(q(e.getClass().getName() + ": " + e.getMessage())).append(",\n");
            b.append("      \"pathIdentity\": {\"identical\": false, \"reason\": \"instrumented run threw\"}\n");
            e.printStackTrace(System.err);
            return b.toString();
        }

        b.append("      \"mechanism\": {\n");
        b.append("        \"note\": \"Read off the ProgressiveLoanInterestScheduleModel the oracle's own ProgressiveLoanScheduleGenerator built and mutated. Nothing here is computed by this harness.\",\n");
        if (captured[0] == null) {
            b.append("        \"modelCaptured\": false,\n        \"periods\": []\n      },\n");
        } else {
            b.append("        \"modelCaptured\": true,\n");
            b.append("        \"periods\": [\n");
            final List<String> mr = new ArrayList<>();
            int idx = 0;
            for (RepaymentPeriod rp : captured[0].repaymentPeriods()) {
                mr.add("          {\"idx\": " + idx
                        + ", \"fromDate\": \"" + rp.getFromDate() + "\", \"dueDate\": \"" + rp.getDueDate()
                        + "\", \"emi\": \"" + pl(rp.getEmi().getAmount())
                        + "\", \"futureUnrecognizedInterest\": \"" + pl(rp.getFutureUnrecognizedInterest().getAmount())
                        + "\", \"interestMovedUpward\": " + rp.isInterestMovedUpward()
                        + ", \"calculatedDueInterest\": \"" + pl(rp.getCalculatedDueInterest().getAmount())
                        + "\", \"dueInterest\": \"" + pl(rp.getDueInterest().getAmount())
                        + "\", \"unrecognizedInterest\": \"" + pl(rp.getUnrecognizedInterest().getAmount())
                        + "\", \"duePrincipal\": \"" + pl(rp.getDuePrincipal().getAmount())
                        + "\", \"outstandingLoanBalance\": \"" + pl(rp.getOutstandingLoanBalance().getAmount())
                        + "\", \"totalPaidAmount\": \"" + pl(rp.getTotalPaidAmount().getAmount())
                        + "\", \"isFullyPaid\": " + rp.isFullyPaid() + "}");
                idx++;
            }
            b.append(String.join(",\n", mr)).append("\n");
            b.append("        ]\n      },\n");
        }

        // PATH IDENTITY — every cell of both plans, rendered by the same code path.
        final String seamRendered = renderPlan(seamPlan);
        final String probeRendered = renderPlan(probePlan);
        b.append("      \"pathIdentity\": {\n");
        b.append("        \"identical\": ").append(seamRendered.equals(probeRendered)).append(",\n");
        b.append("        \"seamPlan\": ").append(q(seamRendered)).append(",\n");
        b.append("        \"instrumentedPlan\": ").append(q(probeRendered)).append("\n");
        b.append("      }\n");
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
                        .append(pl(dpp.getOutstandingLoanBalance())).append(':').append(pl(dpp.getTotalDueAmount()))
                        .append(':').append(pl(dpp.getTotalOutstandingLoanBalance()));
            } else if (p instanceof LoanSchedulePlanRepaymentPeriod rp) {
                s.append("//R:").append(rp.periodNumber()).append(':').append(rp.periodFromDate()).append(':')
                        .append(rp.periodDueDate()).append(':').append(pl(rp.getPrincipalAmount())).append(':')
                        .append(pl(rp.getInterestAmount())).append(':').append(pl(rp.getFeeAmount())).append(':')
                        .append(pl(rp.getPenaltyAmount())).append(':').append(pl(rp.getTotalDueAmount())).append(':')
                        .append(pl(rp.getOutstandingLoanBalance())).append(':')
                        .append(pl(rp.getTotalOutstandingLoanBalance()));
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
     * NOT modified and its byte identity against the pinned original is still asserted by the
     * runner.
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
