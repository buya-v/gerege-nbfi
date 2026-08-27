/*
 * Golden-vector capture harness, PASS 3c — gerege-nbfi Fineract→Go migration, Tier 0.
 *
 * PASS 3c IS PASS 3b's RIG, POINTED AT THE EMI RE-ADJUST SMOOTHING LOOP. Every precondition,
 * attestation field, column and emission rule of Capture3c.java is preserved byte-for-byte below;
 * only the case list differs. Nothing was weakened to get a capture out.
 *
 * WHY THIS PASS EXISTS. Task T9's independent review, finding F-2 (P1): DEC-1 makes the loop
 * checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods (ProgressiveEMICalculator.java:1258-1309,
 * guard EmiAdjustment.java:31-44) a normative conformance obligation, "not backlog"
 * (contract.go:1660-1661) — and NONE of the eleven promoted parity vectors trips its guard. The
 * closest, P-MNT-4M999, misses by one minor unit (|Δ| 8 against a threshold of floor(18/2) = 9).
 * So a Go port that omits the loop entirely passes 11 of 11. DEC-1 names two shapes at
 * contract.go:1655-1658 that DO trip it; this pass captures them at the ratified production
 * MathContext through the pass-3b rig so they can be promoted and the loop can be graded.
 *
 * TWO DISTINCT ROLES, DELIBERATELY BOTH PRESENT — do not conflate them:
 *
 *   P-CAL      RIG CALIBRATION at (12, HALF_UP). Inputs are IDENTICAL to pass 3b's P-CAL, tenant id
 *              included, so its whole observed block must reproduce the committed pass-3b artefact
 *              digit for digit. It is NOT a parity vector and is on PIN.json's never-promotable list.
 *   P-CAL-P00  RIG CALIBRATION at the PRODUCTION (19, HALF_UP). Inputs are IDENTICAL to pass 3b's
 *              P-00, tenant id included, so its whole observed block must reproduce the committed
 *              pass-3b artefact digit for digit AT THE PRECISION THE NEW SHAPES RUN AT. A rig that
 *              cannot reproduce an already-known value is not trustworthy; a precision-12
 *              calibration alone would not cover the precision the parity candidates use.
 *              It is NOT a parity vector.
 *   P-EMI-*    the two parity candidates, at production (19, HALF_UP).
 *
 * It asserts nothing and predicts nothing — every value printed is what the oracle emitted. No
 * expected value is ever synthesised here. In particular this harness does NOT compute the guard,
 * does NOT compute a no-loop counterfactual and does NOT decide whether a shape trips: it prints
 * the oracle's schedule and stops.
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
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.io.File;
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

public class Capture3c {

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

    public static void main(String[] args) throws Exception {
        final List<Case> cases = new ArrayList<>();

        // ---- RIG CALIBRATIONS — reproduce values ALREADY OBSERVED in the committed corpus ------
        // Inputs below are byte-identical to pass 3b's, TENANT ID INCLUDED, so the whole observed
        // block of each must equal the committed .softhouse/capture/out/capture-prod3b-raw.json
        // entry of the same id. If either differs, nothing else from this run is trustworthy.
        cases.add(prod("P-CAL", "RIG CALIBRATION at (12, HALF_UP) — inputs identical to pass 3b P-CAL; must reproduce it digit for digit; NOT a parity vector",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 12, null, false, "usd", "cap_p_cal"));

        cases.add(prod("P-CAL-P00", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) — inputs identical to pass 3b P-00; must reproduce it digit for digit at the precision the parity candidates run at; NOT a parity vector",
                BigDecimal.valueOf(100), 6, BigDecimal.valueOf(7.0), 19, null, false, "usd", "cap_p_00"));

        // ---- PARITY CANDIDATES — the two shapes DEC-1 names at contract.go:1655-1658 ------------
        // Strictly inside the graded domain: single disbursement on the schedule start date,
        // RepaymentEvery 1 MONTHS, DECLINING_BALANCE, DAYS_30/DAYS_360, no down payment, no
        // installment rounding, MNT 2 decimals. Identical in every other respect to the eleven
        // already-promoted parity vectors; only principal, term and rate move.
        cases.add(prod("P-EMI-6-1M014632", "EMI RE-ADJUST SMOOTHING LOOP: MNT 1,014,632 / 6 x 7.0% at PRODUCTION (19, HALF_UP) — DEC-1 contract.go:1656-1657 records the guard tripping here",
                new BigDecimal("1014632"), 6, new BigDecimal("7.0"), 19, null, false, "MNT", "cap_p_emi_6"));

        cases.add(prod("P-EMI-36-127704", "EMI RE-ADJUST SMOOTHING LOOP: MNT 127,704 / 36 x 16.8% at PRODUCTION (19, HALF_UP) — DEC-1 contract.go:1658 records the guard tripping here",
                new BigDecimal("127704"), 36, new BigDecimal("16.8"), 19, null, false, "MNT", "cap_p_emi_36"));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"pass\": \"3c\",\n");
        sb.append("  \"harness\": \"Capture3c.java\",\n");
        sb.append("  \"extends\": \"Capture3b.java / capture-prod3b-raw.json — same rig, same columns, same attestation, same emission rules; a NEW case list targeting the EMI re-adjust smoothing loop (T9 finding F-2). P-CAL and P-CAL-P00 have inputs IDENTICAL to pass 3b's P-CAL and P-00 and must reproduce them digit for digit.\",\n");
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
        try (InputStream in = Capture3c.class.getResourceAsStream("/git.properties")) {
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
                ? "/cap/src/Capture3c.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java"
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
                ? "/cap/out/capture-prod3c-classpath-sha256.txt" : System.getenv("ATTEST_CLASSPATH_OUT");
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
        b.append("      }\n");
        b.append("    }");
        return b.toString();
    }
}
