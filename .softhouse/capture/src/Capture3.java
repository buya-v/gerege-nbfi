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
 *
 * T25 REVISION (2026-08-18), applying the T21 pass-3 audit P0 list
 * (.softhouse/reviews/T21-capture-pass3-audit.md §10):
 *
 *   P0-2  A machine-readable "attestation" object is now emitted at the top level. Everything under
 *         attestation.observedInContainer is READ AT CAPTURE TIME by this JVM, inside the pinned image
 *         (JVM string, MoneyHelper.PRECISION, the jar's own git.properties, SHA-256 of the two compiled
 *         sources and of the provider jar, and a scan of the classpath for prohibited DB drivers).
 *         Facts this JVM cannot see (the image digest, the host checkout commit) are injected by the
 *         runner as -Dcap.host.* system properties and are emitted under attestation.observedOnHost,
 *         kept SEPARATE so a reader can tell what was observed where. Nothing is assumed; a field the
 *         runner did not supply is emitted as null, never as a plausible default.
 *   P0-3  periodFromDate, feeAmount and penaltyAmount are now emitted per period, and the plan-level
 *         totalPrincipalAmount / totalFeeAmount / totalPenaltyAmount / totalOutstandingAmount are
 *         emitted too. They exist on the oracle's own objects (LoanSchedulePlan.java:38-43,70,74-75;
 *         LoanSchedulePlanRepaymentPeriod.java:29,33-34) and were simply dropped by the pass-3 emitter.
 *   P1-9  Every BigDecimal is emitted through toPlainString() (no scientific notation can escape), and
 *         the error branch now retains the top stack frames instead of discarding them.
 *
 * No case, no input and no arithmetic changed. This revision only widens what is RECORDED.
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

import java.io.InputStream;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Properties;

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
        b.append("        \"disbursementAmount\": ").append(money(c.principal())).append(",\n");
        b.append("        \"numberOfRepayments\": ").append(c.noRepayments()).append(",\n");
        b.append("        \"repaymentFrequency\": 1,\n");
        b.append("        \"repaymentFrequencyType\": \"MONTHS\",\n");
        b.append("        \"annualNominalInterestRate\": ").append(money(c.annualRate())).append(",\n");
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
        b.append("        \"downPaymentPercentage\": ").append(money(c.downPaymentPct())).append(",\n");
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
            // T25 / T18 P1-5: the stack trace is EVIDENCE. Keep the top frames instead of discarding them.
            final StringBuilder frames = new StringBuilder();
            final StackTraceElement[] st = e.getStackTrace();
            for (int i = 0; i < Math.min(12, st.length); i++) {
                if (i != 0) {
                    frames.append(", ");
                }
                frames.append("\"").append(esc(st[i].toString())).append("\"");
            }
            b.append("      \"observed\": null,\n");
            b.append("      \"error\": \"").append(esc(e.getClass().getName() + ": " + e.getMessage()))
                    .append("\",\n");
            b.append("      \"errorStackTop\": [").append(frames).append("]\n");
            b.append("    }");
            return b.toString();
        }

        b.append("      \"observed\": {\n");
        b.append("        \"loanTermInDays\": ").append(plan.getLoanTermInDays()).append(",\n");
        b.append("        \"totalDisbursedAmount\": ").append(money(plan.getTotalDisbursedAmount())).append(",\n");
        b.append("        \"totalPrincipalAmount\": ").append(money(plan.getTotalPrincipalAmount())).append(",\n");
        b.append("        \"totalInterestAmount\": ").append(money(plan.getTotalInterestAmount())).append(",\n");
        b.append("        \"totalFeeAmount\": ").append(money(plan.getTotalFeeAmount())).append(",\n");
        b.append("        \"totalPenaltyAmount\": ").append(money(plan.getTotalPenaltyAmount())).append(",\n");
        b.append("        \"totalRepaymentAmount\": ").append(money(plan.getTotalRepaymentAmount())).append(",\n");
        b.append("        \"totalOutstandingAmount\": ").append(money(plan.getTotalOutstandingAmount())).append(",\n");
        b.append("        \"periods\": [\n");

        final List<String> rows = new ArrayList<>();
        for (LoanSchedulePlanPeriod period : plan.getPeriods()) {
            if (period instanceof LoanSchedulePlanDisbursementPeriod dp) {
                rows.add("          {\"type\": \"DISBURSEMENT\", \"periodFromDate\": \"" + dp.periodFromDate()
                        + "\", \"dueDate\": \"" + dp.periodDueDate()
                        + "\", \"principal\": " + money(dp.getPrincipalAmount())
                        + ", \"balance\": " + money(dp.getOutstandingLoanBalance()) + "}");
            } else if (period instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                rows.add("          {\"type\": \"DOWN_PAYMENT\", \"periodNumber\": " + dpp.periodNumber()
                        + ", \"periodFromDate\": \"" + dpp.periodFromDate()
                        + "\", \"dueDate\": \"" + dpp.periodDueDate() + "\", \"balance\": "
                        + money(dpp.getOutstandingLoanBalance()) + ", \"principal\": " + money(dpp.getPrincipalAmount())
                        + ", \"total\": " + money(dpp.getTotalDueAmount()) + ", \"totalOutstandingBalance\": "
                        + money(dpp.getTotalOutstandingLoanBalance()) + "}");
            } else if (period instanceof LoanSchedulePlanRepaymentPeriod rp) {
                rows.add("          {\"type\": \"REPAYMENT\", \"periodNumber\": " + rp.periodNumber()
                        + ", \"periodFromDate\": \"" + rp.periodFromDate()
                        + "\", \"dueDate\": \"" + rp.periodDueDate() + "\", \"balance\": "
                        + money(rp.getOutstandingLoanBalance()) + ", \"principal\": " + money(rp.getPrincipalAmount())
                        + ", \"interest\": " + money(rp.getInterestAmount())
                        + ", \"fee\": " + money(rp.getFeeAmount())
                        + ", \"penalty\": " + money(rp.getPenaltyAmount())
                        + ", \"total\": " + money(rp.getTotalDueAmount()) + ", \"totalOutstandingBalance\": "
                        + money(rp.getTotalOutstandingLoanBalance()) + "}");
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

    // ---------------------------------------------------------------------------------------------
    // T25: emission helpers and the capture-time environment attestation (T21 audit P0-2, plan 4.1).
    // ---------------------------------------------------------------------------------------------

    /** Emit a BigDecimal as a JSON string in PLAIN notation, or the JSON literal null. */
    static String money(final BigDecimal v) {
        return v == null ? "null" : "\"" + v.toPlainString() + "\"";
    }

    /** Minimal JSON string-body escaper. */
    static String esc(final String v) {
        if (v == null) {
            return "";
        }
        return v.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", " ").replace("\r", " ").replace("\t", " ");
    }

    /** A JSON string literal, or the JSON literal null when the value is absent. Never invents a default. */
    static String jstr(final String v) {
        return v == null ? "null" : "\"" + esc(v) + "\"";
    }

    static String sha256(final Path path) {
        try (InputStream in = Files.newInputStream(path)) {
            final MessageDigest md = MessageDigest.getInstance("SHA-256");
            final byte[] buf = new byte[65536];
            int n = in.read(buf);
            while (n != -1) {
                md.update(buf, 0, n);
                n = in.read(buf);
            }
            final StringBuilder hex = new StringBuilder();
            for (byte x : md.digest()) {
                hex.append(String.format(Locale.ROOT, "%02x", x));
            }
            return hex.toString();
        } catch (Exception e) {
            // Honesty rule: a digest we could not take is reported as unreadable, never guessed.
            return "UNREADABLE: " + e.getClass().getSimpleName() + ": " + e.getMessage();
        }
    }

    static String joinQuoted(final List<String> xs) {
        final StringBuilder b = new StringBuilder();
        for (int i = 0; i < xs.size(); i++) {
            if (i != 0) {
                b.append(", ");
            }
            b.append(jstr(xs.get(i)));
        }
        return b.toString();
    }

    /**
     * The environment-attestation block required by the capture plan 4.1 and by T21 audit P0-2.
     *
     * observedInContainer - read by THIS JVM, inside the pinned image, at capture time.
     * observedOnHost      - supplied by the runner via -Dcap.host.*; a value the runner did not supply
     *                       is emitted as null. This JVM cannot see the image digest or the host git
     *                       checkout, and does not pretend to.
     */
    static String attestation() {
        final StringBuilder a = new StringBuilder();
        a.append("  \"attestation\": {\n");
        a.append("    \"capturePath\": \"Path A - embeddable seam, in-process, no database\",\n");
        a.append("    \"capturedAtUtc\": \"").append(Instant.now()).append("\",\n");
        a.append("    \"observedInContainer\": {\n");
        a.append("      \"jvm\": ").append(jstr(System.getProperty("java.runtime.name") + " "
                + System.getProperty("java.runtime.version") + " / " + System.getProperty("java.vm.name") + " "
                + System.getProperty("java.vm.version"))).append(",\n");
        a.append("      \"javaVendor\": ").append(jstr(System.getProperty("java.vendor"))).append(",\n");
        a.append("      \"osArch\": ")
                .append(jstr(System.getProperty("os.name") + " " + System.getProperty("os.arch"))).append(",\n");
        a.append("      \"jvmDefaultTimeZone\": ").append(jstr(java.util.TimeZone.getDefault().getID())).append(",\n");
        a.append("      \"moneyHelperPrecision\": ").append(MoneyHelper.PRECISION).append(",\n");

        // The provider jar's OWN build attestation, read off the classpath.
        final Properties git = new Properties();
        String gitRead = "read";
        try (InputStream in = Capture3.class.getResourceAsStream("/git.properties")) {
            if (in == null) {
                gitRead = "ABSENT: /git.properties is not on the classpath";
            } else {
                git.load(in);
            }
        } catch (Exception e) {
            gitRead = "UNREADABLE: " + e.getClass().getSimpleName() + ": " + e.getMessage();
        }
        a.append("      \"jarGitProperties\": {\n");
        a.append("        \"status\": ").append(jstr(gitRead)).append(",\n");
        a.append("        \"git.commit.id\": ").append(jstr(git.getProperty("git.commit.id"))).append(",\n");
        a.append("        \"git.dirty\": ").append(jstr(git.getProperty("git.dirty"))).append(",\n");
        a.append("        \"git.build.time\": ").append(jstr(git.getProperty("git.build.time"))).append("\n");
        a.append("      },\n");

        // SHA-256 of exactly what was compiled, and of the provider jar the classpath came from.
        final Map<String, String> digests = new LinkedHashMap<>();
        digests.put("/cap/src/Capture3.java", sha256(Paths.get("/cap/src/Capture3.java")));
        digests.put("/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java",
                sha256(Paths.get("/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java")));
        digests.put("/app/fineract-provider.jar", sha256(Paths.get("/app/fineract-provider.jar")));
        a.append("      \"sha256\": {\n");
        int i = 0;
        for (Map.Entry<String, String> e : digests.entrySet()) {
            a.append("        ").append(jstr(e.getKey())).append(": ").append(jstr(e.getValue()));
            i = i + 1;
            a.append(i < digests.size() ? ",\n" : "\n");
        }
        a.append("      },\n");

        // Classpath: count the entries, and ASSERT the PostgreSQL-only rule on the jars actually loaded.
        final String[] cp = String.valueOf(System.getProperty("java.class.path")).split(":");
        final List<String> prohibited = new ArrayList<>();
        final List<String> pg = new ArrayList<>();
        for (String entry : cp) {
            final String lower = entry.toLowerCase(Locale.ROOT);
            if (lower.contains("ojdbc") || lower.contains("oracle") || lower.contains("mysql")
                    || lower.contains("mariadb")) {
                prohibited.add(entry);
            }
            if (lower.contains("postgresql")) {
                pg.add(entry);
            }
        }
        a.append("      \"classpathEntryCount\": ").append(cp.length).append(",\n");
        a.append("      \"classpathPostgresqlEntries\": [").append(joinQuoted(pg)).append("],\n");
        a.append("      \"classpathProhibitedDbEntries\": [").append(joinQuoted(prohibited)).append("],\n");
        a.append("      \"databaseConnections\": \"none - this seam opens no database connection; the harness")
                .append(" references no JDBC or JPA type\"\n");
        a.append("    },\n");

        a.append("    \"observedOnHost\": {\n");
        a.append("      \"note\": \"supplied by the runner via -Dcap.host.*; null means the runner did not supply it\",\n");
        final String[] hostKeys = { "imageDigest", "fineractCommit", "fineractWorktreeClean", "seamByteIdentity",
                "runnerScript", "capturedAtUtc" };
        for (int k = 0; k < hostKeys.length; k++) {
            a.append("      ").append(jstr(hostKeys[k])).append(": ")
                    .append(jstr(System.getProperty("cap.host." + hostKeys[k])));
            a.append(k < hostKeys.length - 1 ? ",\n" : "\n");
        }
        a.append("    }\n");
        a.append("  },\n");
        return a.toString();
    }
}
