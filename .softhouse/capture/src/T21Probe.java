/*
 * T21 AUDIT PROBE — NOT a capture pass, NOT a vector source.
 *
 * Written by the INDEPENDENT REVIEWER of capture pass 3 to test claims that pass 3's own
 * artefacts cannot settle. Everything it prints is OBSERVED oracle output from the pinned
 * image sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a
 * (Fineract commit 426a23544e8426a38ae43ae404670a0a7e85b9eb), run in-process (Path A).
 *
 * Nothing here may be promoted to .softhouse/vectors/. These are AUDIT PROBES.
 *
 * Sections:
 *   A  Reflective proof of the two DROPPED INPUTS at production (19, HALF_UP):
 *      A1 installmentAmountInMultiplesOf — no Builder setter exists, so assembleFrom cannot set it
 *      A2 daysInYearCustomStrategy       — Builder setter IS called (:604) but the private
 *                                          constructor (:304-351) never copies the field
 *   B  Discriminating power of those two inputs at production settings
 *   C  Confirmation runs for the p12-vs-p19 "size threshold" claim in PASS3-REPORT.md
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
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.data.LoanSchedulePlanRepaymentPeriod;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.EmbeddableProgressiveLoanScheduleGenerator;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanApplicationTerms;
import org.apache.fineract.portfolio.loanaccount.loanschedule.domain.LoanRepaymentScheduleModelData;
import org.apache.fineract.portfolio.loanproduct.domain.InterestMethod;

import java.lang.reflect.Field;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.LocalDate;

public class T21Probe {

    static final LocalDate D = LocalDate.of(2024, 1, 1);

    static LoanRepaymentScheduleModelData cfg(BigDecimal principal, int n, BigDecimal rate, String code, int decimals,
            Integer currencyInMultiplesOf, Integer installmentMultiplesOf, DaysInMonthType dim, DaysInYearType diy,
            DaysInYearCustomStrategyType diyCustom, LocalDate start) {
        CurrencyData cur = new CurrencyData(code, code, decimals, currencyInMultiplesOf, code, code);
        return new LoanRepaymentScheduleModelData(start, cur, principal, start, n, 1, "MONTHS", rate, false, dim, diy,
                BigDecimal.ZERO, installmentMultiplesOf, null, false, diyCustom, InterestMethod.DECLINING_BALANCE, true, false);
    }

    static String render(MathContext mc, LoanRepaymentScheduleModelData c) {
        try {
            LoanSchedulePlan p = new EmbeddableProgressiveLoanScheduleGenerator().generate(mc, c);
            StringBuilder b = new StringBuilder();
            b.append("term=").append(p.getLoanTermInDays()).append(" disb=").append(p.getTotalDisbursedAmount())
                    .append(" int=").append(p.getTotalInterestAmount()).append(" rep=").append(p.getTotalRepaymentAmount())
                    .append(" |");
            for (LoanSchedulePlanPeriod q : p.getPeriods()) {
                if (q instanceof LoanSchedulePlanRepaymentPeriod r) {
                    b.append(" #").append(r.periodNumber()).append(":").append(r.getPrincipalAmount()).append("/")
                            .append(r.getInterestAmount()).append("/").append(r.getTotalDueAmount()).append("/")
                            .append(r.getOutstandingLoanBalance());
                } else if (q instanceof LoanSchedulePlanDisbursementPeriod d) {
                    b.append(" D:").append(d.getPrincipalAmount());
                }
            }
            return b.toString();
        } catch (RuntimeException e) {
            StringBuilder b = new StringBuilder("EXCEPTION ").append(e.getClass().getName()).append(": ").append(e.getMessage());
            StackTraceElement[] st = e.getStackTrace();
            for (int i = 0; i < Math.min(5, st.length); i++) {
                b.append("\n        at ").append(st[i]);
            }
            return b.toString();
        }
    }

    static void tenant(String id) {
        ThreadLocalContextUtil.setTenant(new FineractPlatformTenant(1L, id, id, "Asia/Ulaanbaatar", null));
        MoneyHelper.initializeTenantRoundingMode(id, 4); // HALF_UP
    }

    public static void main(String[] args) throws Exception {
        tenant("t21_probe");
        final MathContext P19 = new MathContext(19, RoundingMode.HALF_UP);
        final MathContext P12 = new MathContext(12, RoundingMode.HALF_UP);

        System.out.println("MoneyHelper.PRECISION      = " + MoneyHelper.PRECISION);
        System.out.println("MoneyHelper.getMathContext = " + MoneyHelper.getMathContext());
        System.out.println("java.version               = " + System.getProperty("java.version")
                + " / " + System.getProperty("java.vm.name") + " / " + System.getProperty("java.vendor"));
        System.out.println("code source of Money       = "
                + org.apache.fineract.organisation.monetary.domain.Money.class.getProtectionDomain().getCodeSource());

        // ---------------- A. the two dropped inputs, reflectively, at (19, HALF_UP) -------------
        System.out.println("\n===== A. DROPPED INPUTS — reflective observation at (19, HALF_UP) =====");
        LoanRepaymentScheduleModelData md = cfg(new BigDecimal("5000000"), 18, new BigDecimal("18.5"), "MNT", 2,
                null, 1000, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, DaysInYearCustomStrategyType.FULL_LEAP_YEAR, D);
        System.out.println("model input installmentAmountInMultiplesOf = " + md.installmentAmountInMultiplesOf());
        System.out.println("model input daysInYearCustomStrategy       = " + md.daysInYearCustomStrategy());
        LoanApplicationTerms t = LoanApplicationTerms.assembleFrom(md, P19);
        for (String fn : new String[] { "installmentAmountInMultiplesOf", "daysInYearCustomStrategy" }) {
            Field f = LoanApplicationTerms.class.getDeclaredField(fn);
            f.setAccessible(true);
            System.out.println("assembleFrom(...) -> LoanApplicationTerms." + fn + " = " + f.get(t));
        }

        // ---------------- B. discriminating power at production settings ------------------------
        System.out.println("\n===== B1. installmentAmountInMultiplesOf, decimals=2 (production MNT) =====");
        for (Integer m : new Integer[] { null, 100, 1000, 100000 }) {
            System.out.println("  imo=" + m + "  " + render(P19,
                    cfg(new BigDecimal("5000000"), 18, new BigDecimal("18.5"), "MNT", 2, null, m,
                            DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null, D)));
        }

        System.out.println("\n===== B2. CurrencyData.inMultiplesOf, decimals=2 vs decimals=0 (Money.java:48-51) =====");
        for (int dec : new int[] { 2, 0 }) {
            for (Integer m : new Integer[] { null, 100 }) {
                System.out.println("  decimals=" + dec + " currencyInMultiplesOf=" + m + "  " + render(P19,
                        cfg(new BigDecimal("5000000"), 18, new BigDecimal("18.5"), "MNT", dec, m, null,
                                DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null, D)));
            }
        }

        System.out.println("\n===== B3. daysInYearCustomStrategy at DaysInYearType.ACTUAL over leap 2024 =====");
        for (DaysInYearCustomStrategyType s : new DaysInYearCustomStrategyType[] { null,
                DaysInYearCustomStrategyType.FULL_LEAP_YEAR, DaysInYearCustomStrategyType.FEB_29_PERIOD_ONLY }) {
            System.out.println("  strategy=" + s + "  " + render(P19,
                    cfg(new BigDecimal("5000000"), 18, new BigDecimal("18.5"), "MNT", 2, null, null,
                            DaysInMonthType.ACTUAL, DaysInYearType.ACTUAL, s, D)));
        }

        // ---------------- C. size-threshold confirmation ----------------------------------------
        System.out.println("\n===== C. p12 vs p19 — is there a SIZE THRESHOLD? =====");
        Object[][] cases = {
                { "6 x 7.0%",    6,  "7.0",  new String[] { "100", "245000", "43810", "43811", "43812", "87654321" } },
                { "18 x 18.5%", 18,  "18.5", new String[] { "100", "245000", "138187", "138188", "5000000", "87654321" } },
                { "36 x 16.8%", 36,  "16.8", new String[] { "4", "100", "340", "736", "6940", "50000000" } },
        };
        for (Object[] cs : cases) {
            System.out.println("\n  --- " + cs[0] + " ---");
            int n = (Integer) cs[1];
            BigDecimal rate = new BigDecimal((String) cs[2]);
            for (String ps : (String[]) cs[3]) {
                BigDecimal P = new BigDecimal(ps);
                String a = render(P12, cfg(P, n, rate, "MNT", 2, null, null, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null, D));
                String b = render(P19, cfg(P, n, rate, "MNT", 2, null, null, DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360, null, D));
                System.out.println("    principal=" + ps + "  p12==p19 ? " + (a.equals(b) ? "SAME" : "*** DIFFERENT ***"));
                if (!a.equals(b)) {
                    System.out.println("      p12: " + a);
                    System.out.println("      p19: " + b);
                }
            }
        }
    }
}
