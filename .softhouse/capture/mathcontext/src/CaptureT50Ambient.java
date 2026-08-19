/*
 * T50 TIER 1 -- SEPARATING THE AMBIENT ROUNDING MODE FROM THE THREADED ONE.
 *
 * Runs the PINNED reference oracle (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb,
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a) IN PROCESS.
 * Every class exercised below -- Money, MoneyHelper, MathUtil, CurrencyData -- is loaded from
 * /app/fineract-provider.jar inside that image.  This harness copies NO Fineract source.
 *
 * IT ASSERTS NOTHING AND PREDICTS NOTHING.  Every value printed is what the oracle emitted,
 * rendered with BigDecimal.toPlainString() -- never through a float, never rounded by this
 * harness, never scientific notation.
 *
 * WHY THIS EXISTS.  Two open findings say the same thing:
 *
 *   N46-1  ProgressiveLoanScheduleGenerator.java:445-446 (calculateInstallmentCharge) and
 *          :464-465 (calculateSpecificDueDateChargeWithPercentage) divide under the THREADED
 *          `mc` and then hand the quotient to the TWO-ARGUMENT Money.of(currency, amount)
 *          [Money.java:114-116], which injects MoneyHelper.getMathContext(); the scale-2
 *          rounding at Money.java:52 then runs under THAT context's mode.
 *
 *   N46-3  MathUtil.percentageOf(BigDecimal, BigDecimal, int) [MathUtil.java:472-473] builds
 *          `new MathContext(precision, MoneyHelper.getRoundingMode())`, so a caller passing a
 *          literal precision takes the AMBIENT rounding mode.
 *
 * WHY A TENANT WRITE COULD NOT HAVE SETTLED IT.  On Path B the ambient context IS the threaded
 * object: LoanScheduleAssembler.java:753 does `final MathContext mc = MoneyHelper.getMathContext();`
 * and :765 passes that very reference to generate(mc, ...).  Moving the tenant's rounding mode
 * moves both together.  Only an IN-PROCESS run can set ambient = X and thread (19, Y) with
 * Y != X.  MoneyHelper.initializeTenantRoundingMode is public static and writes a plain
 * ConcurrentHashMap [MoneyHelper.java:54-64], so this needs no server and no database.
 *
 * THE DECISIVE PROBE IS ABSENCE AS WELL AS DIFFERENCE (patterns.md, T46-N2).  Cases whose
 * ambient ordinal is null set a tenant into ThreadLocalContextUtil and NEVER initialise
 * MoneyHelper for it.  MoneyHelper.getRoundingMode() then throws
 *     IllegalStateException: Rounding mode is not initialized for tenant: <id>
 * [MoneyHelper.java:74-82].  A site that reads the ambient context MUST throw; a site that
 * does not read it MUST NOT.  That pair localises the leak without relying on a rounding tie.
 *
 * MONEY RULE.  Integer/BigDecimal exact text, no float or double anywhere in this harness.
 */
import org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant;
import org.apache.fineract.infrastructure.core.service.MathUtil;
import org.apache.fineract.infrastructure.core.service.ThreadLocalContextUtil;
import org.apache.fineract.organisation.monetary.data.CurrencyData;
import org.apache.fineract.organisation.monetary.domain.Money;
import org.apache.fineract.organisation.monetary.domain.MoneyHelper;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;

public class CaptureT50Ambient {

    /** Sentinel: do NOT initialise MoneyHelper for this case's tenant. */
    static final Integer AMBIENT_ABSENT = null;

    /** RoundingMode ordinals, transcribed from java.math.RoundingMode. Verified at runtime below. */
    static final int[] MODE_ORDINALS = { 0, 1, 2, 3, 4, 5, 6 };

    /**
     * A probed SITE. `source` is the file:line the expression is transcribed from; `readsAmbient`
     * is NOT an assertion -- it is this harness's HYPOTHESIS, printed so the observation can
     * contradict it, and the runner script cross-checks the observation against it.
     */
    record Site(String id, String source, String expression, boolean hypothesisReadsAmbient) {
    }

    /** An input pair. `a` is the base amount/value; `pct` is the percentage. Exact decimal text. */
    record Val(String name, String a, String pct, String why) {
    }

    record Case(String id, Site site, Val val, Integer ambientOrdinal, int threadedPrecision, int threadedOrdinal) {
    }

    // ---------------------------------------------------------------------------------------
    // SITES
    // ---------------------------------------------------------------------------------------

    static final Site S1 = new Site("S1-CHARGE-2ARG",
            "ProgressiveLoanScheduleGenerator.java:445-446 (calculateInstallmentCharge)",
            "Money.of(currency, amount.multiply(pct).divide(BigDecimal.valueOf(100), mc))", true);

    static final Site S2 = new Site("S2-CHARGE-3ARG",
            "COUNTERFACTUAL -- what :445-446 would do if the threaded mc were passed to Money.of",
            "Money.of(currency, amount.multiply(pct).divide(BigDecimal.valueOf(100), mc), mc)", false);

    static final Site S3 = new Site("S3-PCTOF-INT19", "MathUtil.java:472-473 via a literal precision of 19",
            "MathUtil.percentageOf(a, pct, 19)", true);

    static final Site S4 = new Site("S4-DOWNPAYMENT-LAT866",
            "LoanApplicationTerms.java:865-866 (down payment amount)",
            "Money.of(currency, MathUtil.percentageOf(a, pct, 19))", true);

    static final Site S5 = new Site("S5-PCTOF-MC",
            "COUNTERFACTUAL -- MathUtil.java:484-491, the MathContext overload, threaded",
            "MathUtil.percentageOf(a, pct, new MathContext(19, threadedMode))", false);

    static final Site S6 = new Site("S6-SPECIFICDUE-2ARG",
            "ProgressiveLoanScheduleGenerator.java:464-465 (calculateSpecificDueDateChargeWithPercentage)",
            "Money.of(currency, amount.multiply(pct).divide(BigDecimal.valueOf(100), mc))", true);

    static final List<Site> SITES = List.of(S1, S2, S3, S4, S5, S6);

    // ---------------------------------------------------------------------------------------
    // VALUES.  Chosen so the ROUNDING STEP UNDER TEST lands on an exact tie.
    // ---------------------------------------------------------------------------------------

    static final List<Val> VALS = List.of(
            new Val("V1-tie-scale2-even", "100.50", "1",
                    "a*pct/100 = 1.005 exactly; scale-2 tie, last kept digit 0 (even)"),
            new Val("V2-tie-scale2-odd", "100.50", "3",
                    "a*pct/100 = 3.015 exactly; scale-2 tie, last kept digit 1 (odd)"),
            new Val("V3-noTie-scale2", "100.00", "1",
                    "a*pct/100 = 1.0000 exactly; NULL CONTROL -- no rounding decision exists at scale 2"),
            new Val("V4-tie-scale2-mnt", "4020100.50", "25",
                    "a*pct/100 = 1005025.125 exactly; MNT-sized scale-2 tie, last kept digit 2 (even)"),
            new Val("V5-tie-prec19-even", "12345678901234567.885", "10",
                    "a*pct/100 = 1234567890123456.7885, 20 significant digits; tie at 19, last kept 8 (even)"),
            new Val("V6-tie-prec19-odd", "12345678901234567.875", "10",
                    "a*pct/100 = 1234567890123456.7875, 20 significant digits; tie at 19, last kept 7 (odd)"));

    // MNT: ISO 4217 numeric 496, minor unit 2.  inMultiplesOf null so Money's roundToMultiplesOf
    // branch [Money.java:46-50] cannot fire and cannot confound the scale-2 rounding.
    static CurrencyData mnt() {
        return new CurrencyData("MNT", "Mongolian Togrog", 2, null, "MNT", "MNT");
    }

    // ---------------------------------------------------------------------------------------

    static List<Case> cases() {
        final List<Case> out = new ArrayList<>();
        // The ambient axis carries the seven RoundingMode ordinals plus ABSENT (uninitialised).
        final List<Integer> ambients = new ArrayList<>();
        for (int o : MODE_ORDINALS) {
            ambients.add(o);
        }
        ambients.add(AMBIENT_ABSENT);

        for (Site site : SITES) {
            for (Val v : VALS) {
                for (Integer amb : ambients) {
                    for (int thr : MODE_ORDINALS) {
                        final String id = site.id() + "__" + v.name() + "__A" + (amb == null ? "ABSENT" : String.valueOf(amb))
                                + "__T" + thr;
                        out.add(new Case(id, site, v, amb, 19, thr));
                    }
                }
            }
        }
        return out;
    }

    /**
     * Proves the ABSENCE PROBE IS LIVE, not vacuous (patterns.md / T46-N2). Sets a tenant that
     * MoneyHelper was never initialised for and reads the ambient context directly. If this does
     * NOT throw, every ABSENT case below is meaningless and the run MUST be rejected.
     */
    static String ambientCanary() {
        final String tenantId = "t50_canary_never_initialised";
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenantId, tenantId, "Asia/Ulaanbaatar", null));
        try {
            return "NO THROW -- ambient read succeeded: " + MoneyHelper.getMathContext();
        } catch (RuntimeException e) {
            return "THREW " + e.getClass().getName() + ": " + esc(String.valueOf(e.getMessage()));
        }
    }

    /**
     * Proves the ordinal->RoundingMode mapping this harness relies on is the oracle's own, read
     * back out of MoneyHelper rather than assumed from the JDK docs.
     */
    static String ordinalProof() {
        final StringBuilder sb = new StringBuilder();
        for (int o = 0; o <= 7; o++) {
            final String tenantId = "t50_ordinal_" + o;
            ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenantId, tenantId, "Asia/Ulaanbaatar", null));
            String seen;
            try {
                MoneyHelper.initializeTenantRoundingMode(tenantId, o);
                seen = String.valueOf(MoneyHelper.getRoundingMode());
            } catch (RuntimeException e) {
                seen = "THREW " + e.getClass().getName() + ": " + esc(String.valueOf(e.getMessage()));
            }
            if (o > 0) {
                sb.append(",\n");
            }
            sb.append("      { \"ordinal\": ").append(o).append(", \"moneyHelperRoundingMode\": \"").append(seen)
                    .append("\", \"jdkRoundingModeValues\": \"")
                    .append(o < RoundingMode.values().length ? RoundingMode.values()[o].name() : "OUT_OF_RANGE").append("\" }");
        }
        return sb.toString();
    }

    static String esc(String s) {
        return s == null ? ""
                : s.replace("\\", "\\\\").replace("\"", "'").replace("\n", " | ").replace("\r", " ").replace("\t", " ");
    }

    // ---------------------------------------------------------------------------------------

    static String run(final Case c) {
        // A UNIQUE tenant id per case.  MoneyHelper caches per tenant id [MoneyHelper.java:37-38],
        // so this makes the cases independent and lets the ABSENT cases have a genuinely
        // uninitialised tenant.
        final String tenantId = "t50_" + c.id().toLowerCase().replace('-', '_').replace("__", "_");
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, tenantId, tenantId, "Asia/Ulaanbaatar", null));
        if (c.ambientOrdinal() != null) {
            MoneyHelper.initializeTenantRoundingMode(tenantId, c.ambientOrdinal());
        }

        // Echo the ambient context OFF THE OBJECT (T46 audit finding M-5), not off the intent.
        String ambientEcho;
        try {
            ambientEcho = String.valueOf(MoneyHelper.getMathContext());
        } catch (RuntimeException e) {
            ambientEcho = "THREW " + e.getClass().getName() + ": " + esc(String.valueOf(e.getMessage()));
        }
        // NOTE: for an initialised tenant the read above populates MoneyHelper's mathContextCache;
        // for an ABSENT case it throws and leaves both caches empty, which is what the probe needs.

        final MathContext mc = new MathContext(c.threadedPrecision(), RoundingMode.values()[c.threadedOrdinal()]);
        final CurrencyData currency = mnt();
        final BigDecimal a = new BigDecimal(c.val().a());
        final BigDecimal pct = new BigDecimal(c.val().pct());

        final StringBuilder b = new StringBuilder();
        b.append("    {\n");
        b.append("      \"id\": \"").append(c.id()).append("\",\n");
        b.append("      \"site\": \"").append(c.site().id()).append("\",\n");
        b.append("      \"siteSource\": \"").append(esc(c.site().source())).append("\",\n");
        b.append("      \"siteExpression\": \"").append(esc(c.site().expression())).append("\",\n");
        b.append("      \"hypothesisReadsAmbient\": ").append(c.site().hypothesisReadsAmbient()).append(",\n");
        b.append("      \"value\": \"").append(c.val().name()).append("\",\n");
        b.append("      \"valueWhy\": \"").append(esc(c.val().why())).append("\",\n");
        b.append("      \"inputs\": {\n");
        b.append("        \"a\": \"").append(a.toPlainString()).append("\",\n");
        b.append("        \"percentage\": \"").append(pct.toPlainString()).append("\",\n");
        b.append("        \"currencyCode\": \"MNT\",\n");
        b.append("        \"currencyDecimalPlaces\": 2,\n");
        b.append("        \"currencyInMultiplesOf\": null,\n");
        b.append("        \"tenantId\": \"").append(tenantId).append("\",\n");
        b.append("        \"ambientRoundingModeOrdinal\": ")
                .append(c.ambientOrdinal() == null ? "null" : String.valueOf(c.ambientOrdinal())).append(",\n");
        b.append("        \"ambientRoundingModeIntent\": \"")
                .append(c.ambientOrdinal() == null ? "ABSENT" : RoundingMode.values()[c.ambientOrdinal()].name()).append("\",\n");
        b.append("        \"threadedPrecisionIntent\": ").append(c.threadedPrecision()).append(",\n");
        b.append("        \"threadedRoundingModeOrdinal\": ").append(c.threadedOrdinal()).append(",\n");
        b.append("        \"threadedRoundingModeIntent\": \"").append(RoundingMode.values()[c.threadedOrdinal()].name())
                .append("\"\n");
        b.append("      },\n");
        // Attestation read OFF THE OBJECTS.
        b.append("      \"attestation\": {\n");
        b.append("        \"ambientMathContextObject\": \"").append(esc(ambientEcho)).append("\",\n");
        b.append("        \"threadedMathContextObject\": \"").append(mc).append("\",\n");
        b.append("        \"threadedPrecisionObject\": ").append(mc.getPrecision()).append(",\n");
        b.append("        \"threadedRoundingModeObject\": \"").append(mc.getRoundingMode().name()).append("\",\n");
        b.append("        \"ambientEqualsThreadedObject\": ").append(ambientEcho.equals(String.valueOf(mc))).append("\n");
        b.append("      },\n");

        String observed = null;
        String intermediate = null;
        String error = null;
        String stack = null;
        try {
            switch (c.site().id()) {
                case "S1-CHARGE-2ARG", "S6-SPECIFICDUE-2ARG" -> {
                    // Transcribed from ProgressiveLoanScheduleGenerator.java:445-446 / :464-465.
                    final BigDecimal q = a.multiply(pct).divide(BigDecimal.valueOf(100), mc);
                    intermediate = q.toPlainString();
                    final Money m = Money.of(currency, q);
                    observed = m.getAmount().toPlainString();
                }
                case "S2-CHARGE-3ARG" -> {
                    final BigDecimal q = a.multiply(pct).divide(BigDecimal.valueOf(100), mc);
                    intermediate = q.toPlainString();
                    final Money m = Money.of(currency, q, mc);
                    observed = m.getAmount().toPlainString();
                }
                case "S3-PCTOF-INT19" -> {
                    final BigDecimal r = MathUtil.percentageOf(a, pct, 19);
                    observed = r.toPlainString();
                }
                case "S4-DOWNPAYMENT-LAT866" -> {
                    // Transcribed from LoanApplicationTerms.java:865-866.
                    final BigDecimal r = MathUtil.percentageOf(a, pct, 19);
                    intermediate = r.toPlainString();
                    final Money m = Money.of(currency, r);
                    observed = m.getAmount().toPlainString();
                }
                case "S5-PCTOF-MC" -> {
                    final BigDecimal r = MathUtil.percentageOf(a, pct, mc);
                    observed = r.toPlainString();
                }
                default -> throw new IllegalStateException("unknown site " + c.site().id());
            }
        } catch (RuntimeException | StackOverflowError e) {
            final StringWriter sw = new StringWriter();
            e.printStackTrace(new PrintWriter(sw));
            error = e.getClass().getName() + ": " + esc(String.valueOf(e.getMessage()));
            stack = esc(sw.toString());
        }

        b.append("      \"intermediate\": ").append(intermediate == null ? "null" : "\"" + intermediate + "\"").append(",\n");
        b.append("      \"observed\": ").append(observed == null ? "null" : "\"" + observed + "\"").append(",\n");
        b.append("      \"error\": ").append(error == null ? "null" : "\"" + error + "\"").append(",\n");
        b.append("      \"stackTrace\": ").append(stack == null ? "null" : "\"" + stack + "\"").append("\n");
        b.append("    }");
        return b.toString();
    }

    public static void main(String[] args) {
        final List<Case> cs = cases();
        final StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"harness\": \"T50 CaptureT50Ambient -- ambient vs threaded RoundingMode, in process\",\n");
        sb.append("  \"oracleCommit\": \"426a23544e8426a38ae43ae404670a0a7e85b9eb\",\n");
        sb.append("  \"moneyHelperPrecisionConstant\": ").append(MoneyHelper.PRECISION).append(",\n");
        sb.append("  \"ambientCanary\": \"").append(ambientCanary()).append("\",\n");
        sb.append("  \"ordinalProof\": [\n").append(ordinalProof()).append("\n  ],\n");
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
