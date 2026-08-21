/*
 * CaptureT177 — a TRIAL RUNNER for task T177, gerege-nbfi Fineract→Go migration, gate G-8.
 *
 * THE QUESTION
 * ------------
 * T159 observed the cell (B = 10001 minor units, n = 3000, annual rate 600.0) CLEANLY
 * [VERIFIED: .softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz -> id
 * T159-R600p0-N3000-B10001, totalInterestAmount 846.70]. T169 asked the SAME cell on the SAME
 * pinned image and the reference oracle threw java.lang.StackOverflowError
 * [VERIFIED: .softhouse/capture/src/t169-red/out/capture-t169-Post.json -> id
 * T169-TWIN-R600p0-N3000-B10001, errorClass java.lang.StackOverflowError]. So whether the oracle
 * throws is NOT a function of the cell's inputs alone. This harness measures WHAT ELSE IT IS A
 * FUNCTION OF, by asking the same cell MANY TIMES under controlled variations.
 *
 * WHAT IT IS NOT
 * --------------
 * It is not a capture rig and it PROMOTES NOTHING. It computes money values only so that (a) the
 * two committed rig calibrations can prove it is calling the same seam as every other rig in this
 * program, and (b) an observed disputed cell can be checked against T159's committed 846.70. No
 * value here is a parity vector and none may be promoted.
 *
 * MONEY. Principals are INTEGER MINOR UNITS, emitted as new BigDecimal(<int>).movePointLeft(2).
 * There is no floating-point literal, field or intermediate anywhere in this file.
 *
 * SETTINGS. Production: MathContext (19, HALF_UP), tenant rounding ordinal 4 — MoneyHelper.PRECISION
 * is a compile-time 19 [MoneyHelper.java:35, 91-93]. Every trial runs at it.
 *
 * THE SEAM CALL, the Case record, prodDates() and every input field are copied VERBATIM from the
 * committed CaptureT169Post.java so that a trial here is the same evaluation T169 and T159 made.
 * The ONLY differences are the OUTPUT SHAPE (one JSON object per line, so 150 trials do not emit
 * 450,000 period rows) and the TRIAL PLAN driver.
 *
 * THROW HANDLING is delegated to the shared .softhouse/capture/lib/ThrewOutcome.java (T169):
 * catch (Throwable), isFatal() re-throws VirtualMachineError-other-than-SOE / ThreadDeath /
 * LinkageError, and appendThrew() writes the recorded fields. The recorded field NAMES are
 * therefore identical to T169's capture shape.
 *
 * PostgreSQL is the only permitted database in this program. This harness opens no database
 * connection and starts no Fineract server. "The oracle" here is the Fineract reference
 * implementation, never Oracle Database, which is a prohibited product in this program.
 *
 * USAGE:  java CaptureT177 <plan>
 *   single                 1 probe trial of the disputed cell, on the main thread
 *   repeat:K               K probe trials of the disputed cell, on the main thread
 *   warm:M:K               M warm trials of the CTRL cell (n=200, same principal), then K probes
 *   t159prefix:K           T159's committed case list in T159's committed ORDER up to (and not
 *                          including) the disputed cell, then K probes
 *   thread:BYTES:K         K probe trials, each on a FRESHLY SPAWNED thread of stackSize BYTES
 *                          (0 = the JVM default for a new thread)
 *   calib                  the two committed rig calibrations, with full period rows, so the
 *                          analyzer can prove this rig reproduces pass 3g cell for cell
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

import java.lang.management.ManagementFactory;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class CaptureT177 {

    // ---- VERBATIM from CaptureT169Post.java (record + prodDates), so a trial is the same call ----
    record Case(String id, String purpose, LocalDate startDate, LocalDate disbursementDate, BigDecimal principal,
            int noRepayments, BigDecimal annualRate, int precision, RoundingMode mode, String currencyCode,
            int currencyDigits, DaysInMonthType dim, DaysInYearType diy, DaysInYearCustomStrategyType diyCustom,
            BigDecimal downPaymentPct, Integer currencyMultiplesOf, Integer installmentMultiplesOf,
            Integer fixedLength,
            boolean interestRecognitionOnDisbursementDate, boolean allowPartialPeriodInterestCalculation,
            boolean allowFullTermForTranche, String tenantId, Integer tenantRoundingMode) {
    }

    static Case prodDates(String id, String purpose, LocalDate startDate, LocalDate disbursementDate,
            BigDecimal principal, int noRepayments, BigDecimal rate, String tenantId) {
        return new Case(id, purpose, startDate, disbursementDate, principal, noRepayments, rate, 19,
                RoundingMode.HALF_UP, "MNT", 2, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null,
                BigDecimal.ZERO, null, null, null, false, true, false, tenantId, 4);
    }

    static final LocalDate D = LocalDate.of(2024, 1, 1);

    /** money in INTEGER MINOR UNITS -> BigDecimal, never a decimal literal, never a float. */
    static BigDecimal minor(int minorUnits) {
        return new BigDecimal(minorUnits).movePointLeft(2);
    }

    static Case cell(String id, int principalMinor, int n, String rate, String tenant) {
        return prodDates(id, "T177 trial", D, D, minor(principalMinor), n, new BigDecimal(rate), tenant);
    }

    /** THE DISPUTED CELL. B = 10001 minor units, n = 3000, annual rate 600.0. */
    static Case disputed() {
        return cell("T177-PROBE-R600p0-N3000-B10001", 10001, 3000, "600.0", "t177_probe_n3000_b10001");
    }

    /** The CTRL warmer: same principal and rate, n = 200 — a term no run in this program has seen throw. */
    static Case ctrl() {
        return cell("T177-WARM-R600p0-N200-B10001", 10001, 200, "600.0", "t177_warm_n200_b10001");
    }

    // ------------------------------------------------------------------------------------------
    public static void main(String[] args) throws Exception {
        final String plan = args.length > 0 ? args[0] : "single";
        final String series = env("T177_SERIES", "unnamed");
        final String runIdx = env("T177_RUN_IDX", "0");

        StringBuilder h = new StringBuilder();
        h.append("{\"kind\": \"header\"");
        h.append(", \"series\": ").append(q(series));
        h.append(", \"runIdx\": ").append(q(runIdx));
        h.append(", \"plan\": ").append(q(plan));
        h.append(", \"startedAtUtc\": ").append(q(Instant.now().toString()));
        h.append(", \"javaVersion\": ").append(q(System.getProperty("java.version")));
        h.append(", \"javaVmName\": ").append(q(System.getProperty("java.vm.name")));
        h.append(", \"javaVmVersion\": ").append(q(System.getProperty("java.vm.version")));
        h.append(", \"jvmInputArguments\": ")
                .append(q(String.join(" ", ManagementFactory.getRuntimeMXBean().getInputArguments())));
        h.append(", \"availableProcessors\": ").append(Runtime.getRuntime().availableProcessors());
        h.append(", \"moneyHelperPrecision\": ").append(MoneyHelper.PRECISION);
        h.append(", \"attestEcho\": {\"imageRef\": ").append(q(System.getenv("ATTEST_IMAGE_REF")));
        h.append(", \"imageId\": ").append(q(System.getenv("ATTEST_IMAGE_ID")));
        h.append(", \"pinnedCommit\": ").append(q(System.getenv("ATTEST_PINNED_COMMIT")));
        h.append(", \"harnessSha256\": ").append(q(System.getenv("ATTEST_HARNESS_SHA")));
        h.append(", \"seamSha256\": ").append(q(System.getenv("ATTEST_SEAM_SHA")));
        h.append(", \"libSha256\": ").append(q(System.getenv("ATTEST_LIB_SHA")));
        h.append(", \"runId\": ").append(q(System.getenv("ATTEST_RUN_ID")));
        h.append("}}");
        System.out.println(h);

        final int[] seq = { 0 };
        if (plan.equals("calib")) {
            emit(series, runIdx, plan, seq, "calib", "main", -1L,
                    prodDates("P-CAL-ZPA", "T177 rig calibration — inputs byte-identical to pass 3g T64-ZP-A", D, D,
                            new BigDecimal("0.28"), 56, new BigDecimal("21.6"), "cap_t64_zp_a"),
                    true);
            emit(series, runIdx, plan, seq, "calib", "main", -1L,
                    prodDates("P-CAL-ZPB", "T177 rig calibration — inputs byte-identical to pass 3g T64-ZP-B", D, D,
                            new BigDecimal("0.28"), 55, new BigDecimal("21.6"), "cap_t64_zp_b"),
                    true);
        } else if (plan.equals("single")) {
            emit(series, runIdx, plan, seq, "probe", "main", -1L, disputed(), false);
        } else if (plan.startsWith("repeat:")) {
            int k = Integer.parseInt(plan.substring("repeat:".length()));
            for (int i = 0; i < k; i++) {
                emit(series, runIdx, plan, seq, "probe", "main", -1L, disputed(), false);
            }
        } else if (plan.startsWith("warm:")) {
            String[] p = plan.split(":");
            int m = Integer.parseInt(p[1]);
            int k = Integer.parseInt(p[2]);
            for (int i = 0; i < m; i++) {
                emit(series, runIdx, plan, seq, "warm", "main", -1L, ctrl(), false);
            }
            for (int i = 0; i < k; i++) {
                emit(series, runIdx, plan, seq, "probe", "main", -1L, disputed(), false);
            }
        } else if (plan.startsWith("t159prefix:")) {
            int k = Integer.parseInt(plan.substring("t159prefix:".length()));
            for (Case c : t159Prefix()) {
                emit(series, runIdx, plan, seq, "prefix", "main", -1L, c, false);
            }
            for (int i = 0; i < k; i++) {
                emit(series, runIdx, plan, seq, "probe", "main", -1L, disputed(), false);
            }
        } else if (plan.startsWith("thread:")) {
            String[] p = plan.split(":");
            final long ss = Long.parseLong(p[1]);
            int k = Integer.parseInt(p[2]);
            for (int i = 0; i < k; i++) {
                final int[] localSeq = { seq[0] };
                final String[] out = { null };
                Thread t = new Thread(null,
                        () -> out[0] = trialLine(series, runIdx, plan, localSeq, "probe", "spawned", ss, disputed(),
                                false),
                        "t177-trial", ss);
                t.start();
                t.join();
                seq[0] = localSeq[0];
                if (out[0] == null) {
                    // A spawned thread that produced no line is a RIG ERROR, not an outcome. It is
                    // emitted as its own kind so the analyzer can never fold it into observed/threw.
                    System.out.println("{\"kind\": \"trial\", \"series\": " + q(series) + ", \"runIdx\": " + q(runIdx)
                            + ", \"plan\": " + q(plan) + ", \"seq\": " + seq[0]
                            + ", \"phase\": \"probe\", \"thread\": \"spawned\", \"threadStackSizeRequested\": " + ss
                            + ", \"cellId\": \"T177-PROBE-R600p0-N3000-B10001\", \"outcome\": \"rig-error\","
                            + " \"rigError\": \"spawned thread produced no line\"}");
                    seq[0]++;
                } else {
                    System.out.println(out[0]);
                }
            }
        } else {
            throw new IllegalArgumentException("unknown plan: " + plan);
        }

        System.out.println("{\"kind\": \"footer\", \"series\": " + q(series) + ", \"runIdx\": " + q(runIdx)
                + ", \"plan\": " + q(plan) + ", \"trialsEmitted\": " + seq[0] + ", \"finishedAtUtc\": "
                + q(Instant.now().toString()) + "}");
    }

    static void emit(String series, String runIdx, String plan, int[] seq, String phase, String thread, long ss,
            Case c, boolean withPeriods) {
        System.out.println(trialLine(series, runIdx, plan, seq, phase, thread, ss, c, withPeriods));
    }

    /**
     * T159's committed sweep order, up to but NOT including T159-R600p0-N3000-B10001, which sits at
     * index 26 of the sweep (index 28 of the run, after the two calibrations). Every (principal, n)
     * pair below is copied from the committed CaptureT159.java case list; the tenant ids are T177's
     * own so nothing here can be a replay of a T159 anything.
     */
    static List<Case> t159Prefix() {
        int[][] pairs = {
            // {principal in MINOR UNITS, numberOfRepayments} — T159's order, cases 1..26 of the sweep
            { 10001, 2000 }, { 1, 401 }, { 1, 392 }, { 501, 2000 }, { 100001, 3000 }, { 1, 1200 },
            { 1001, 1200 }, { 1, 2000 }, { 1, 400 }, { 1001, 1500 }, { 1, 391 }, { 1, 361 },
            { 10001, 1200 }, { 11, 108 }, { 11, 150 }, { 1001, 3000 }, { 1, 389 }, { 10001, 1500 },
            { 901, 1000 }, { 503, 1000 }, { 1, 364 }, { 1, 360 }, { 999, 2000 }, { 1, 3000 },
        };
        List<Case> out = new ArrayList<>();
        for (int[] p : pairs) {
            String id = "T177-PREFIX-R600p0-N" + p[1] + "-B" + p[0];
            out.add(cell(id, p[0], p[1], "600.0", "t177_prefix_n" + p[1] + "_b" + p[0]));
        }
        return out;
    }

    // ------------------------------------------------------------------------------------------
    /** ONE trial. Returns the JSON object for it as a SINGLE LINE. */
    static String trialLine(String series, String runIdx, String plan, int[] seq, String phase, String thread, long ss,
            final Case c, boolean withPeriods) {
        final int mySeq = seq[0]++;

        ThreadLocalContextUtil
                .setTenant(new FineractPlatformTenant(1L, c.tenantId(), c.tenantId(), "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(c.tenantId(), c.tenantRoundingMode());
        MathContext ambient = MoneyHelper.getMathContext();

        final MathContext mc = new MathContext(c.precision(), c.mode());
        final EmbeddableProgressiveLoanScheduleGenerator generator = new EmbeddableProgressiveLoanScheduleGenerator();
        final CurrencyData currency = new CurrencyData(c.currencyCode(), c.currencyCode(), c.currencyDigits(),
                c.currencyMultiplesOf(), c.currencyCode(), c.currencyCode());
        final LoanRepaymentScheduleModelData config = new LoanRepaymentScheduleModelData(c.startDate(), currency,
                c.principal(), c.disbursementDate(), c.noRepayments(), 1, "MONTHS", c.annualRate(),
                BigDecimal.ZERO.compareTo(c.downPaymentPct()) != 0, c.dim(), c.diy(), c.downPaymentPct(),
                c.installmentMultiplesOf(), c.fixedLength(), c.interestRecognitionOnDisbursementDate(), c.diyCustom(),
                InterestMethod.DECLINING_BALANCE, c.allowPartialPeriodInterestCalculation(),
                c.allowFullTermForTranche());

        final StringBuilder b = new StringBuilder();
        b.append("{\"kind\": \"trial\"");
        b.append(", \"series\": ").append(q(series));
        b.append(", \"runIdx\": ").append(q(runIdx));
        b.append(", \"plan\": ").append(q(plan));
        b.append(", \"seq\": ").append(mySeq);
        b.append(", \"phase\": ").append(q(phase));
        b.append(", \"thread\": ").append(q(thread));
        b.append(", \"threadName\": ").append(q(Thread.currentThread().getName()));
        b.append(", \"threadStackSizeRequested\": ").append(ss);
        b.append(", \"cellId\": ").append(q(c.id()));
        b.append(", \"principalMinorUnits\": ").append(c.principal().movePointRight(2).toPlainString());
        b.append(", \"numberOfRepayments\": ").append(c.noRepayments());
        b.append(", \"annualNominalInterestRate\": ").append(q(c.annualRate().toPlainString()));
        b.append(", \"mathContextPrecision\": ").append(c.precision());
        b.append(", \"mathContextRoundingMode\": ").append(q(c.mode().name()));
        b.append(", \"ambientMoneyHelperMathContext\": ").append(q(String.valueOf(ambient)));
        b.append(", \"tenantId\": ").append(q(c.tenantId()));
        b.append(", ");

        final long t0 = System.nanoTime();
        final LoanSchedulePlan schedulePlan;
        try {
            schedulePlan = generator.generate(mc, config);
        } catch (Throwable t) {
            // T169's shared rule. Throwable, NOT RuntimeException: java.lang.StackOverflowError is
            // an Error and is precisely the throwable the pre-T169 handler could not see.
            final long msT = (System.nanoTime() - t0) / 1000000L;
            if (ThrewOutcome.isFatal(t)) {
                ThrewOutcome.announceFatal(c.id(), t);
                throw t;
            }
            StringBuilder tb = new StringBuilder();
            ThrewOutcome.appendThrew(tb, t, 6);
            b.append("\"elapsedMs\": ").append(msT).append(", ");
            b.append(flatten(tb.toString()));
            return b.toString();
        }
        final long ms = (System.nanoTime() - t0) / 1000000L;

        b.append("\"elapsedMs\": ").append(ms);
        b.append(", \"outcome\": \"observed\", \"observed\": {");
        b.append("\"loanTermInDays\": ").append(schedulePlan.getLoanTermInDays());
        b.append(", \"totalDisbursedAmount\": ").append(q(pl(schedulePlan.getTotalDisbursedAmount())));
        b.append(", \"totalPrincipalAmount\": ").append(q(pl(schedulePlan.getTotalPrincipalAmount())));
        b.append(", \"totalInterestAmount\": ").append(q(pl(schedulePlan.getTotalInterestAmount())));
        b.append(", \"totalFeeAmount\": ").append(q(pl(schedulePlan.getTotalFeeAmount())));
        b.append(", \"totalPenaltyAmount\": ").append(q(pl(schedulePlan.getTotalPenaltyAmount())));
        b.append(", \"totalRepaymentAmount\": ").append(q(pl(schedulePlan.getTotalRepaymentAmount())));
        b.append(", \"totalOutstandingAmount\": ").append(q(pl(schedulePlan.getTotalOutstandingAmount())));
        b.append(", \"periodCount\": ").append(schedulePlan.getPeriods().size());
        if (withPeriods) {
            final List<String> rows = new ArrayList<>();
            for (LoanSchedulePlanPeriod period : schedulePlan.getPeriods()) {
                if (period instanceof LoanSchedulePlanDisbursementPeriod dp) {
                    rows.add("{\"type\": \"DISBURSEMENT\", \"periodFromDate\": \"" + dp.periodFromDate()
                            + "\", \"dueDate\": \"" + dp.periodDueDate() + "\", \"principal\": \""
                            + pl(dp.getPrincipalAmount()) + "\", \"balance\": \"" + pl(dp.getOutstandingLoanBalance())
                            + "\"}");
                } else if (period instanceof LoanSchedulePlanDownPaymentPeriod dpp) {
                    rows.add("{\"type\": \"DOWN_PAYMENT\", \"periodNumber\": " + dpp.periodNumber()
                            + ", \"periodFromDate\": \"" + dpp.periodFromDate() + "\", \"dueDate\": \""
                            + dpp.periodDueDate() + "\", \"balance\": \"" + pl(dpp.getOutstandingLoanBalance())
                            + "\", \"principal\": \"" + pl(dpp.getPrincipalAmount()) + "\", \"total\": \""
                            + pl(dpp.getTotalDueAmount()) + "\", \"totalOutstandingBalance\": \""
                            + pl(dpp.getTotalOutstandingLoanBalance()) + "\"}");
                } else if (period instanceof LoanSchedulePlanRepaymentPeriod rp) {
                    rows.add("{\"type\": \"REPAYMENT\", \"periodNumber\": " + rp.periodNumber()
                            + ", \"periodFromDate\": \"" + rp.periodFromDate() + "\", \"dueDate\": \""
                            + rp.periodDueDate() + "\", \"balance\": \"" + pl(rp.getOutstandingLoanBalance())
                            + "\", \"principal\": \"" + pl(rp.getPrincipalAmount()) + "\", \"interest\": \""
                            + pl(rp.getInterestAmount()) + "\", \"feeAmount\": \"" + pl(rp.getFeeAmount())
                            + "\", \"penaltyAmount\": \"" + pl(rp.getPenaltyAmount()) + "\", \"total\": \""
                            + pl(rp.getTotalDueAmount()) + "\", \"totalOutstandingBalance\": \""
                            + pl(rp.getTotalOutstandingLoanBalance()) + "\"}");
                } else {
                    rows.add("{\"type\": \"UNKNOWN:" + period.getClass().getName() + "\"}");
                }
            }
            b.append(", \"periods\": [").append(String.join(", ", rows)).append("]");
        }
        b.append("}}");
        return b.toString();
    }

    /**
     * Collapse ThrewOutcome's multi-line block onto one line WITHOUT altering any token: each line
     * is stripped of its leading/trailing indentation only, then joined with a single space. Interior
     * runs of spaces inside a recorded message or frame are left alone.
     */
    static String flatten(String s) {
        String[] parts = s.split("\n", -1);
        StringBuilder out = new StringBuilder();
        for (String p : parts) {
            String t = p.strip();
            if (t.isEmpty()) {
                continue;
            }
            if (out.length() > 0) {
                out.append(' ');
            }
            out.append(t);
        }
        return out.toString();
    }

    static String env(String k, String dflt) {
        String v = System.getenv(k);
        return v == null ? dflt : v;
    }

    static String pl(BigDecimal d) {
        return d == null ? "null" : d.toPlainString();
    }

    static String esc(String s) {
        return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", " ").replace("\r", " ")
                .replace("\t", " ");
    }

    static String q(String s) {
        return s == null ? "null" : "\"" + esc(s) + "\"";
    }
}
