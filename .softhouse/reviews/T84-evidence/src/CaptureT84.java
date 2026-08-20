/*
 * Golden-vector capture harness, T83 — gerege-nbfi Fineract→Go migration, Tier 0. Gate G-8.
 *
 * THIS IS PASS 3g's RIG WITH A NEW CASE LIST AND PASS 3i's FIELD SPLIT. Every attestation field,
 * every emitted column and every emission rule of Capture3g.java is preserved byte-for-byte, so the
 * `observed` block of a case whose inputs match a pass-3g case must equal pass 3g's committed block
 * cell for cell. That is what makes the two RIG CALIBRATIONS below meaningful. The one structural
 * change is pass 3i's separation of `CurrencyData.inMultiplesOf` from
 * `installmentAmountInMultiplesOf` (T21 required change P1-8); EVERY case here passes null for
 * both, so both keys emit exactly as pass 3g emitted them.
 *
 * WHY THIS PASS EXISTS — task T83, gate G-8. T75 reported that inside DEC-1's graded domain
 * (MinorUnitDigits = 2, (19, HALF_UP), single disbursement on the schedule start date, MONTHS/1,
 * DECLINING_BALANCE, DAYS_30/DAYS_360, no down payment, BOTH multiples-of inputs null) the
 * reference oracle emits a schedule whose outstanding-balance column NEVER REACHES ZERO, and that
 * the Go port returns 0 there. T83 re-measures that INDEPENDENTLY — it takes no number from T75 —
 * and measures the EXACT BOUNDARY by a contiguous sweep.
 *
 * THE SWEEP. For each of four annual rates {21.6, 7.0, 16.8, 36.0} and each of eight repayment
 * counts {2, 3, 4, 6, 12, 24, 36, 56}, the principal is swept over a CONTIGUOUS range of minor
 * units starting at 1 and running past the predicted boundary. Every case is emitted, the clean
 * ones as well as the failing ones: a sweep reported only by its positives is not a boundary, and a
 * hole in the region is only visible if the whole range is present.
 *
 * THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING. It does not know which cases it expects to
 * fail, does not classify them, does not compute an annuity factor and does not compare anything.
 * It asks the oracle for a schedule and prints what came back. The prediction lives in
 * .softhouse/capture/t83-nonamortizing/PREDICTION.md and predicted-boundary.json, committed in an
 * ANCESTOR COMMIT of the one that carries this file, and the classification is done afterwards by
 * classify-boundary.py reading only the emitted JSON.
 *
 * TWO RIG CALIBRATIONS, both ALREADY-PROMOTED parity vectors at the rounding floor at dp 2:
 *
 *   P-CAL-ZPA   inputs byte-identical to pass 3g's T64-ZP-A (MNT 0.28 / 56 x 21.6%), tenant id
 *               included. Longest term and smallest principal in the promoted corpus at the time.
 *   P-CAL-ZPB   inputs byte-identical to pass 3g's T64-ZP-B (MNT 0.28 / 55 x 21.6%), tenant id
 *               included. The ONLY shape in the committed corpus carrying a ZERO-EMI TAIL — i.e.
 *               the nearest committed neighbour of the region this pass measures.
 *
 * Neither is a parity candidate of this pass. If either fails to reproduce pass 3g cell for cell,
 * run-t83.sh refuses the run and nothing else here is believed.
 *
 * PRODUCTION SETTINGS. Buyan ratified the tenant parameters on 2026-08-18: rounding mode HALF_UP,
 * licence NBFI. Precision is not a choice — MoneyHelper.PRECISION = 19 is a compile-time constant and
 * getMathContext() returns new MathContext(19, tenantRoundingMode) [MoneyHelper.java:35, 91-93]. So the
 * PRODUCTION MathContext is (19, HALF_UP). Every case in this pass runs at it.
 *
 * PostgreSQL remains the only permitted database for this program; this seam opens no database
 * connection at all and starts no Fineract server. "The oracle" here is the Fineract reference
 * implementation, never Oracle Database (a prohibited product).
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

public class CaptureT84 {

    /**
     * One capture run. Pass 3g's Case record with pass 3i's ONE structural fix carried over: the
     * two multiples-of inputs are SEPARATE components (T21 required change P1-8). Passes 3..3h
     * spent a single {@code installmentMultiplesOf} field on the 4th argument of
     * {@code new CurrencyData(...)} (which is {@code CurrencyData.inMultiplesOf},
     * Money.java:48-51) AND on the 12th argument of {@code LoanRepaymentScheduleModelData} (which
     * is {@code installmentAmountInMultiplesOf}, ProgressiveEMICalculator.java:1761-1776), so no
     * capture taken through them could attribute a difference to either.
     *
     * EVERY CASE IN THIS HARNESS PASSES **NULL** FOR BOTH, which is what makes the calibration
     * against pass 3g valid: pass 3g emitted both keys from one null field, this harness emits them
     * from two null fields, and the emitted JSON is therefore identical.
     */
    record Case(String id, String purpose, LocalDate startDate, LocalDate disbursementDate, BigDecimal principal,
            int noRepayments, BigDecimal annualRate, int precision, RoundingMode mode, String currencyCode,
            int currencyDigits, DaysInMonthType dim, DaysInYearType diy, DaysInYearCustomStrategyType diyCustom,
            BigDecimal downPaymentPct, Integer currencyMultiplesOf, Integer installmentMultiplesOf,
            Integer fixedLength,
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
                BigDecimal.ZERO, null, installmentMultiplesOf, null, false, true, allowFullTermForTranche, tenantId,
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
                BigDecimal.ZERO, null, null, null, false, true, false, tenantId, 4);
    }

    public static void main(String[] args) throws Exception {
        final List<Case> cases = new ArrayList<>();

        // ---- RIG CALIBRATIONS — reproduce values ALREADY OBSERVED in the committed corpus ------
        // Inputs byte-identical to pass 3g's T64-ZP-A and T64-ZP-B, TENANT ID INCLUDED, so the whole
        // observed block of each must equal the committed entry of the same shape in
        // .softhouse/capture/out/capture-prod3g-raw.json. Both are ALREADY-PROMOTED parity vectors
        // at the rounding floor at dp 2 — the nearest committed neighbours of the region this pass
        // measures. If either differs by one cell, run-t83.sh refuses the run.
        cases.add(prodDates("P-CAL-ZPA", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3g T64-ZP-A, an already-promoted parity vector at the rounding floor; must reproduce it digit for digit; NOT a parity vector and NOT part of the sweep",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 56, new BigDecimal("21.6"), "cap_t64_zp_a"));

        cases.add(prodDates("P-CAL-ZPB", "RIG CALIBRATION at PRODUCTION (19, HALF_UP) in MNT — inputs identical to pass 3g T64-ZP-B, the ONLY shape in the committed corpus carrying a zero-EMI tail; must reproduce it digit for digit; NOT a parity vector and NOT part of the sweep",
                LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal("0.28"), 55, new BigDecimal("21.6"), "cap_t64_zp_b"));

        // ---- T84 INDEPENDENT RE-PROBE CASE LIST (attacks T83, not a copy of its sweep) ----
        cases.add(prodDates("T84-RP-R36p0-N3-B1", "T84 independent re-probe (RP): MNT 0.01 / 3 x 36.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 3, new BigDecimal("36.0"), "t84_rp_r36p0_n3_b1"));
        cases.add(prodDates("T84-RP-R21p6-N56-B18", "T84 independent re-probe (RP): MNT 0.18 / 56 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(18).movePointLeft(2), 56, new BigDecimal("21.6"), "t84_rp_r21p6_n56_b18"));
        cases.add(prodDates("T84-RP-R21p6-N56-B17", "T84 independent re-probe (RP): MNT 0.17 / 56 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(17).movePointLeft(2), 56, new BigDecimal("21.6"), "t84_rp_r21p6_n56_b17"));
        cases.add(prodDates("T84-RP-R21p6-N2-B1", "T84 independent re-probe (RP): MNT 0.01 / 2 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 2, new BigDecimal("21.6"), "t84_rp_r21p6_n2_b1"));
        cases.add(prodDates("T84-RP-R16p8-N24-B11", "T84 independent re-probe (RP): MNT 0.11 / 24 x 16.8%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(11).movePointLeft(2), 24, new BigDecimal("16.8"), "t84_rp_r16p8_n24_b11"));
        cases.add(prodDates("T84-RP-R16p8-N24-B10", "T84 independent re-probe (RP): MNT 0.10 / 24 x 16.8%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10).movePointLeft(2), 24, new BigDecimal("16.8"), "t84_rp_r16p8_n24_b10"));
        cases.add(prodDates("T84-RP-R36p0-N12-B5", "T84 independent re-probe (RP): MNT 0.05 / 12 x 36.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 12, new BigDecimal("36.0"), "t84_rp_r36p0_n12_b5"));
        cases.add(prodDates("T84-RP-R36p0-N12-B4", "T84 independent re-probe (RP): MNT 0.04 / 12 x 36.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 12, new BigDecimal("36.0"), "t84_rp_r36p0_n12_b4"));
        cases.add(prodDates("T84-RP-R7p0-N56-B24", "T84 independent re-probe (RP): MNT 0.24 / 56 x 7.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(24).movePointLeft(2), 56, new BigDecimal("7.0"), "t84_rp_r7p0_n56_b24"));
        cases.add(prodDates("T84-RP-R7p0-N56-B23", "T84 independent re-probe (RP): MNT 0.23 / 56 x 7.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(23).movePointLeft(2), 56, new BigDecimal("7.0"), "t84_rp_r7p0_n56_b23"));
        cases.add(prodDates("T84-RP-R21p6-N6-B3", "T84 independent re-probe (RP): MNT 0.03 / 6 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 6, new BigDecimal("21.6"), "t84_rp_r21p6_n6_b3"));
        cases.add(prodDates("T84-RP-R21p6-N6-B2", "T84 independent re-probe (RP): MNT 0.02 / 6 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 6, new BigDecimal("21.6"), "t84_rp_r21p6_n6_b2"));
        cases.add(prodDates("T84-FAR-R21p6-N6-B30", "T84 independent re-probe (FAR): MNT 0.30 / 6 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(30).movePointLeft(2), 6, new BigDecimal("21.6"), "t84_far_r21p6_n6_b30"));
        cases.add(prodDates("T84-FAR-R21p6-N6-B50", "T84 independent re-probe (FAR): MNT 0.50 / 6 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(50).movePointLeft(2), 6, new BigDecimal("21.6"), "t84_far_r21p6_n6_b50"));
        cases.add(prodDates("T84-FAR-R21p6-N6-B100", "T84 independent re-probe (FAR): MNT 1.00 / 6 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(100).movePointLeft(2), 6, new BigDecimal("21.6"), "t84_far_r21p6_n6_b100"));
        cases.add(prodDates("T84-FAR-R21p6-N6-B1000", "T84 independent re-probe (FAR): MNT 10.00 / 6 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1000).movePointLeft(2), 6, new BigDecimal("21.6"), "t84_far_r21p6_n6_b1000"));
        cases.add(prodDates("T84-FAR-R21p6-N6-B10000", "T84 independent re-probe (FAR): MNT 100.00 / 6 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10000).movePointLeft(2), 6, new BigDecimal("21.6"), "t84_far_r21p6_n6_b10000"));
        cases.add(prodDates("T84-FAR-R21p6-N6-B100000", "T84 independent re-probe (FAR): MNT 1000.00 / 6 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(100000).movePointLeft(2), 6, new BigDecimal("21.6"), "t84_far_r21p6_n6_b100000"));
        cases.add(prodDates("T84-FAR-R7p0-N56-B30", "T84 independent re-probe (FAR): MNT 0.30 / 56 x 7.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(30).movePointLeft(2), 56, new BigDecimal("7.0"), "t84_far_r7p0_n56_b30"));
        cases.add(prodDates("T84-FAR-R7p0-N56-B50", "T84 independent re-probe (FAR): MNT 0.50 / 56 x 7.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(50).movePointLeft(2), 56, new BigDecimal("7.0"), "t84_far_r7p0_n56_b50"));
        cases.add(prodDates("T84-FAR-R7p0-N56-B100", "T84 independent re-probe (FAR): MNT 1.00 / 56 x 7.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(100).movePointLeft(2), 56, new BigDecimal("7.0"), "t84_far_r7p0_n56_b100"));
        cases.add(prodDates("T84-FAR-R7p0-N56-B1000", "T84 independent re-probe (FAR): MNT 10.00 / 56 x 7.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1000).movePointLeft(2), 56, new BigDecimal("7.0"), "t84_far_r7p0_n56_b1000"));
        cases.add(prodDates("T84-FAR-R7p0-N56-B10000", "T84 independent re-probe (FAR): MNT 100.00 / 56 x 7.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10000).movePointLeft(2), 56, new BigDecimal("7.0"), "t84_far_r7p0_n56_b10000"));
        cases.add(prodDates("T84-FAR-R7p0-N56-B100000", "T84 independent re-probe (FAR): MNT 1000.00 / 56 x 7.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(100000).movePointLeft(2), 56, new BigDecimal("7.0"), "t84_far_r7p0_n56_b100000"));
        cases.add(prodDates("T84-FAR-R36p0-N12-B30", "T84 independent re-probe (FAR): MNT 0.30 / 12 x 36.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(30).movePointLeft(2), 12, new BigDecimal("36.0"), "t84_far_r36p0_n12_b30"));
        cases.add(prodDates("T84-FAR-R36p0-N12-B50", "T84 independent re-probe (FAR): MNT 0.50 / 12 x 36.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(50).movePointLeft(2), 12, new BigDecimal("36.0"), "t84_far_r36p0_n12_b50"));
        cases.add(prodDates("T84-FAR-R36p0-N12-B100", "T84 independent re-probe (FAR): MNT 1.00 / 12 x 36.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(100).movePointLeft(2), 12, new BigDecimal("36.0"), "t84_far_r36p0_n12_b100"));
        cases.add(prodDates("T84-FAR-R36p0-N12-B1000", "T84 independent re-probe (FAR): MNT 10.00 / 12 x 36.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1000).movePointLeft(2), 12, new BigDecimal("36.0"), "t84_far_r36p0_n12_b1000"));
        cases.add(prodDates("T84-FAR-R36p0-N12-B10000", "T84 independent re-probe (FAR): MNT 100.00 / 12 x 36.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10000).movePointLeft(2), 12, new BigDecimal("36.0"), "t84_far_r36p0_n12_b10000"));
        cases.add(prodDates("T84-FAR-R36p0-N12-B100000", "T84 independent re-probe (FAR): MNT 1000.00 / 12 x 36.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(100000).movePointLeft(2), 12, new BigDecimal("36.0"), "t84_far_r36p0_n12_b100000"));
        cases.add(prodDates("T84-FAR-R16p8-N36-B30", "T84 independent re-probe (FAR): MNT 0.30 / 36 x 16.8%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(30).movePointLeft(2), 36, new BigDecimal("16.8"), "t84_far_r16p8_n36_b30"));
        cases.add(prodDates("T84-FAR-R16p8-N36-B50", "T84 independent re-probe (FAR): MNT 0.50 / 36 x 16.8%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(50).movePointLeft(2), 36, new BigDecimal("16.8"), "t84_far_r16p8_n36_b50"));
        cases.add(prodDates("T84-FAR-R16p8-N36-B100", "T84 independent re-probe (FAR): MNT 1.00 / 36 x 16.8%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(100).movePointLeft(2), 36, new BigDecimal("16.8"), "t84_far_r16p8_n36_b100"));
        cases.add(prodDates("T84-FAR-R16p8-N36-B1000", "T84 independent re-probe (FAR): MNT 10.00 / 36 x 16.8%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1000).movePointLeft(2), 36, new BigDecimal("16.8"), "t84_far_r16p8_n36_b1000"));
        cases.add(prodDates("T84-FAR-R16p8-N36-B10000", "T84 independent re-probe (FAR): MNT 100.00 / 36 x 16.8%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10000).movePointLeft(2), 36, new BigDecimal("16.8"), "t84_far_r16p8_n36_b10000"));
        cases.add(prodDates("T84-FAR-R16p8-N36-B100000", "T84 independent re-probe (FAR): MNT 1000.00 / 36 x 16.8%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(100000).movePointLeft(2), 36, new BigDecimal("16.8"), "t84_far_r16p8_n36_b100000"));
        cases.add(prodDates("T84-RATE-R1p2-N6-B1", "T84 independent re-probe (RATE): MNT 0.01 / 6 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 6, new BigDecimal("1.2"), "t84_rate_r1p2_n6_b1"));
        cases.add(prodDates("T84-RATE-R1p2-N6-B2", "T84 independent re-probe (RATE): MNT 0.02 / 6 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 6, new BigDecimal("1.2"), "t84_rate_r1p2_n6_b2"));
        cases.add(prodDates("T84-RATE-R1p2-N6-B3", "T84 independent re-probe (RATE): MNT 0.03 / 6 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 6, new BigDecimal("1.2"), "t84_rate_r1p2_n6_b3"));
        cases.add(prodDates("T84-RATE-R1p2-N6-B4", "T84 independent re-probe (RATE): MNT 0.04 / 6 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 6, new BigDecimal("1.2"), "t84_rate_r1p2_n6_b4"));
        cases.add(prodDates("T84-RATE-R1p2-N6-B5", "T84 independent re-probe (RATE): MNT 0.05 / 6 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 6, new BigDecimal("1.2"), "t84_rate_r1p2_n6_b5"));
        cases.add(prodDates("T84-RATE-R1p2-N12-B3", "T84 independent re-probe (RATE): MNT 0.03 / 12 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 12, new BigDecimal("1.2"), "t84_rate_r1p2_n12_b3"));
        cases.add(prodDates("T84-RATE-R1p2-N12-B4", "T84 independent re-probe (RATE): MNT 0.04 / 12 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 12, new BigDecimal("1.2"), "t84_rate_r1p2_n12_b4"));
        cases.add(prodDates("T84-RATE-R1p2-N12-B5", "T84 independent re-probe (RATE): MNT 0.05 / 12 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 12, new BigDecimal("1.2"), "t84_rate_r1p2_n12_b5"));
        cases.add(prodDates("T84-RATE-R1p2-N12-B6", "T84 independent re-probe (RATE): MNT 0.06 / 12 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(6).movePointLeft(2), 12, new BigDecimal("1.2"), "t84_rate_r1p2_n12_b6"));
        cases.add(prodDates("T84-RATE-R1p2-N12-B7", "T84 independent re-probe (RATE): MNT 0.07 / 12 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(7).movePointLeft(2), 12, new BigDecimal("1.2"), "t84_rate_r1p2_n12_b7"));
        cases.add(prodDates("T84-RATE-R1p2-N12-B8", "T84 independent re-probe (RATE): MNT 0.08 / 12 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(8).movePointLeft(2), 12, new BigDecimal("1.2"), "t84_rate_r1p2_n12_b8"));
        cases.add(prodDates("T84-RATE-R1p2-N56-B25", "T84 independent re-probe (RATE): MNT 0.25 / 56 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(25).movePointLeft(2), 56, new BigDecimal("1.2"), "t84_rate_r1p2_n56_b25"));
        cases.add(prodDates("T84-RATE-R1p2-N56-B26", "T84 independent re-probe (RATE): MNT 0.26 / 56 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(26).movePointLeft(2), 56, new BigDecimal("1.2"), "t84_rate_r1p2_n56_b26"));
        cases.add(prodDates("T84-RATE-R1p2-N56-B27", "T84 independent re-probe (RATE): MNT 0.27 / 56 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(27).movePointLeft(2), 56, new BigDecimal("1.2"), "t84_rate_r1p2_n56_b27"));
        cases.add(prodDates("T84-RATE-R1p2-N56-B28", "T84 independent re-probe (RATE): MNT 0.28 / 56 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("1.2"), "t84_rate_r1p2_n56_b28"));
        cases.add(prodDates("T84-RATE-R1p2-N56-B29", "T84 independent re-probe (RATE): MNT 0.29 / 56 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(29).movePointLeft(2), 56, new BigDecimal("1.2"), "t84_rate_r1p2_n56_b29"));
        cases.add(prodDates("T84-RATE-R1p2-N56-B30", "T84 independent re-probe (RATE): MNT 0.30 / 56 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(30).movePointLeft(2), 56, new BigDecimal("1.2"), "t84_rate_r1p2_n56_b30"));
        cases.add(prodDates("T84-RATE-R3p6-N6-B1", "T84 independent re-probe (RATE): MNT 0.01 / 6 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 6, new BigDecimal("3.6"), "t84_rate_r3p6_n6_b1"));
        cases.add(prodDates("T84-RATE-R3p6-N6-B2", "T84 independent re-probe (RATE): MNT 0.02 / 6 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 6, new BigDecimal("3.6"), "t84_rate_r3p6_n6_b2"));
        cases.add(prodDates("T84-RATE-R3p6-N6-B3", "T84 independent re-probe (RATE): MNT 0.03 / 6 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 6, new BigDecimal("3.6"), "t84_rate_r3p6_n6_b3"));
        cases.add(prodDates("T84-RATE-R3p6-N6-B4", "T84 independent re-probe (RATE): MNT 0.04 / 6 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 6, new BigDecimal("3.6"), "t84_rate_r3p6_n6_b4"));
        cases.add(prodDates("T84-RATE-R3p6-N6-B5", "T84 independent re-probe (RATE): MNT 0.05 / 6 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 6, new BigDecimal("3.6"), "t84_rate_r3p6_n6_b5"));
        cases.add(prodDates("T84-RATE-R3p6-N12-B3", "T84 independent re-probe (RATE): MNT 0.03 / 12 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 12, new BigDecimal("3.6"), "t84_rate_r3p6_n12_b3"));
        cases.add(prodDates("T84-RATE-R3p6-N12-B4", "T84 independent re-probe (RATE): MNT 0.04 / 12 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 12, new BigDecimal("3.6"), "t84_rate_r3p6_n12_b4"));
        cases.add(prodDates("T84-RATE-R3p6-N12-B5", "T84 independent re-probe (RATE): MNT 0.05 / 12 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 12, new BigDecimal("3.6"), "t84_rate_r3p6_n12_b5"));
        cases.add(prodDates("T84-RATE-R3p6-N12-B6", "T84 independent re-probe (RATE): MNT 0.06 / 12 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(6).movePointLeft(2), 12, new BigDecimal("3.6"), "t84_rate_r3p6_n12_b6"));
        cases.add(prodDates("T84-RATE-R3p6-N12-B7", "T84 independent re-probe (RATE): MNT 0.07 / 12 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(7).movePointLeft(2), 12, new BigDecimal("3.6"), "t84_rate_r3p6_n12_b7"));
        cases.add(prodDates("T84-RATE-R3p6-N12-B8", "T84 independent re-probe (RATE): MNT 0.08 / 12 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(8).movePointLeft(2), 12, new BigDecimal("3.6"), "t84_rate_r3p6_n12_b8"));
        cases.add(prodDates("T84-RATE-R3p6-N56-B23", "T84 independent re-probe (RATE): MNT 0.23 / 56 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(23).movePointLeft(2), 56, new BigDecimal("3.6"), "t84_rate_r3p6_n56_b23"));
        cases.add(prodDates("T84-RATE-R3p6-N56-B24", "T84 independent re-probe (RATE): MNT 0.24 / 56 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(24).movePointLeft(2), 56, new BigDecimal("3.6"), "t84_rate_r3p6_n56_b24"));
        cases.add(prodDates("T84-RATE-R3p6-N56-B25", "T84 independent re-probe (RATE): MNT 0.25 / 56 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(25).movePointLeft(2), 56, new BigDecimal("3.6"), "t84_rate_r3p6_n56_b25"));
        cases.add(prodDates("T84-RATE-R3p6-N56-B26", "T84 independent re-probe (RATE): MNT 0.26 / 56 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(26).movePointLeft(2), 56, new BigDecimal("3.6"), "t84_rate_r3p6_n56_b26"));
        cases.add(prodDates("T84-RATE-R3p6-N56-B27", "T84 independent re-probe (RATE): MNT 0.27 / 56 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(27).movePointLeft(2), 56, new BigDecimal("3.6"), "t84_rate_r3p6_n56_b27"));
        cases.add(prodDates("T84-RATE-R3p6-N56-B28", "T84 independent re-probe (RATE): MNT 0.28 / 56 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 56, new BigDecimal("3.6"), "t84_rate_r3p6_n56_b28"));
        cases.add(prodDates("T84-RATE-R12p0-N6-B1", "T84 independent re-probe (RATE): MNT 0.01 / 6 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 6, new BigDecimal("12.0"), "t84_rate_r12p0_n6_b1"));
        cases.add(prodDates("T84-RATE-R12p0-N6-B2", "T84 independent re-probe (RATE): MNT 0.02 / 6 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 6, new BigDecimal("12.0"), "t84_rate_r12p0_n6_b2"));
        cases.add(prodDates("T84-RATE-R12p0-N6-B3", "T84 independent re-probe (RATE): MNT 0.03 / 6 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 6, new BigDecimal("12.0"), "t84_rate_r12p0_n6_b3"));
        cases.add(prodDates("T84-RATE-R12p0-N6-B4", "T84 independent re-probe (RATE): MNT 0.04 / 6 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 6, new BigDecimal("12.0"), "t84_rate_r12p0_n6_b4"));
        cases.add(prodDates("T84-RATE-R12p0-N6-B5", "T84 independent re-probe (RATE): MNT 0.05 / 6 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 6, new BigDecimal("12.0"), "t84_rate_r12p0_n6_b5"));
        cases.add(prodDates("T84-RATE-R12p0-N12-B3", "T84 independent re-probe (RATE): MNT 0.03 / 12 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 12, new BigDecimal("12.0"), "t84_rate_r12p0_n12_b3"));
        cases.add(prodDates("T84-RATE-R12p0-N12-B4", "T84 independent re-probe (RATE): MNT 0.04 / 12 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 12, new BigDecimal("12.0"), "t84_rate_r12p0_n12_b4"));
        cases.add(prodDates("T84-RATE-R12p0-N12-B5", "T84 independent re-probe (RATE): MNT 0.05 / 12 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 12, new BigDecimal("12.0"), "t84_rate_r12p0_n12_b5"));
        cases.add(prodDates("T84-RATE-R12p0-N12-B6", "T84 independent re-probe (RATE): MNT 0.06 / 12 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(6).movePointLeft(2), 12, new BigDecimal("12.0"), "t84_rate_r12p0_n12_b6"));
        cases.add(prodDates("T84-RATE-R12p0-N12-B7", "T84 independent re-probe (RATE): MNT 0.07 / 12 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(7).movePointLeft(2), 12, new BigDecimal("12.0"), "t84_rate_r12p0_n12_b7"));
        cases.add(prodDates("T84-RATE-R12p0-N12-B8", "T84 independent re-probe (RATE): MNT 0.08 / 12 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(8).movePointLeft(2), 12, new BigDecimal("12.0"), "t84_rate_r12p0_n12_b8"));
        cases.add(prodDates("T84-RATE-R12p0-N56-B19", "T84 independent re-probe (RATE): MNT 0.19 / 56 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(19).movePointLeft(2), 56, new BigDecimal("12.0"), "t84_rate_r12p0_n56_b19"));
        cases.add(prodDates("T84-RATE-R12p0-N56-B20", "T84 independent re-probe (RATE): MNT 0.20 / 56 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(20).movePointLeft(2), 56, new BigDecimal("12.0"), "t84_rate_r12p0_n56_b20"));
        cases.add(prodDates("T84-RATE-R12p0-N56-B21", "T84 independent re-probe (RATE): MNT 0.21 / 56 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(21).movePointLeft(2), 56, new BigDecimal("12.0"), "t84_rate_r12p0_n56_b21"));
        cases.add(prodDates("T84-RATE-R12p0-N56-B22", "T84 independent re-probe (RATE): MNT 0.22 / 56 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(22).movePointLeft(2), 56, new BigDecimal("12.0"), "t84_rate_r12p0_n56_b22"));
        cases.add(prodDates("T84-RATE-R12p0-N56-B23", "T84 independent re-probe (RATE): MNT 0.23 / 56 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(23).movePointLeft(2), 56, new BigDecimal("12.0"), "t84_rate_r12p0_n56_b23"));
        cases.add(prodDates("T84-RATE-R12p0-N56-B24", "T84 independent re-probe (RATE): MNT 0.24 / 56 x 12.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(24).movePointLeft(2), 56, new BigDecimal("12.0"), "t84_rate_r12p0_n56_b24"));
        cases.add(prodDates("T84-RATE-R48p0-N6-B1", "T84 independent re-probe (RATE): MNT 0.01 / 6 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 6, new BigDecimal("48.0"), "t84_rate_r48p0_n6_b1"));
        cases.add(prodDates("T84-RATE-R48p0-N6-B2", "T84 independent re-probe (RATE): MNT 0.02 / 6 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 6, new BigDecimal("48.0"), "t84_rate_r48p0_n6_b2"));
        cases.add(prodDates("T84-RATE-R48p0-N6-B3", "T84 independent re-probe (RATE): MNT 0.03 / 6 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 6, new BigDecimal("48.0"), "t84_rate_r48p0_n6_b3"));
        cases.add(prodDates("T84-RATE-R48p0-N6-B4", "T84 independent re-probe (RATE): MNT 0.04 / 6 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 6, new BigDecimal("48.0"), "t84_rate_r48p0_n6_b4"));
        cases.add(prodDates("T84-RATE-R48p0-N6-B5", "T84 independent re-probe (RATE): MNT 0.05 / 6 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 6, new BigDecimal("48.0"), "t84_rate_r48p0_n6_b5"));
        cases.add(prodDates("T84-RATE-R48p0-N12-B2", "T84 independent re-probe (RATE): MNT 0.02 / 12 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 12, new BigDecimal("48.0"), "t84_rate_r48p0_n12_b2"));
        cases.add(prodDates("T84-RATE-R48p0-N12-B3", "T84 independent re-probe (RATE): MNT 0.03 / 12 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 12, new BigDecimal("48.0"), "t84_rate_r48p0_n12_b3"));
        cases.add(prodDates("T84-RATE-R48p0-N12-B4", "T84 independent re-probe (RATE): MNT 0.04 / 12 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 12, new BigDecimal("48.0"), "t84_rate_r48p0_n12_b4"));
        cases.add(prodDates("T84-RATE-R48p0-N12-B5", "T84 independent re-probe (RATE): MNT 0.05 / 12 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 12, new BigDecimal("48.0"), "t84_rate_r48p0_n12_b5"));
        cases.add(prodDates("T84-RATE-R48p0-N12-B6", "T84 independent re-probe (RATE): MNT 0.06 / 12 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(6).movePointLeft(2), 12, new BigDecimal("48.0"), "t84_rate_r48p0_n12_b6"));
        cases.add(prodDates("T84-RATE-R48p0-N12-B7", "T84 independent re-probe (RATE): MNT 0.07 / 12 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(7).movePointLeft(2), 12, new BigDecimal("48.0"), "t84_rate_r48p0_n12_b7"));
        cases.add(prodDates("T84-RATE-R48p0-N56-B9", "T84 independent re-probe (RATE): MNT 0.09 / 56 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(9).movePointLeft(2), 56, new BigDecimal("48.0"), "t84_rate_r48p0_n56_b9"));
        cases.add(prodDates("T84-RATE-R48p0-N56-B10", "T84 independent re-probe (RATE): MNT 0.10 / 56 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10).movePointLeft(2), 56, new BigDecimal("48.0"), "t84_rate_r48p0_n56_b10"));
        cases.add(prodDates("T84-RATE-R48p0-N56-B11", "T84 independent re-probe (RATE): MNT 0.11 / 56 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(11).movePointLeft(2), 56, new BigDecimal("48.0"), "t84_rate_r48p0_n56_b11"));
        cases.add(prodDates("T84-RATE-R48p0-N56-B12", "T84 independent re-probe (RATE): MNT 0.12 / 56 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(12).movePointLeft(2), 56, new BigDecimal("48.0"), "t84_rate_r48p0_n56_b12"));
        cases.add(prodDates("T84-RATE-R48p0-N56-B13", "T84 independent re-probe (RATE): MNT 0.13 / 56 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(13).movePointLeft(2), 56, new BigDecimal("48.0"), "t84_rate_r48p0_n56_b13"));
        cases.add(prodDates("T84-RATE-R48p0-N56-B14", "T84 independent re-probe (RATE): MNT 0.14 / 56 x 48.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(14).movePointLeft(2), 56, new BigDecimal("48.0"), "t84_rate_r48p0_n56_b14"));
        cases.add(prodDates("T84-RATE-R96p0-N6-B1", "T84 independent re-probe (RATE): MNT 0.01 / 6 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 6, new BigDecimal("96.0"), "t84_rate_r96p0_n6_b1"));
        cases.add(prodDates("T84-RATE-R96p0-N6-B2", "T84 independent re-probe (RATE): MNT 0.02 / 6 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 6, new BigDecimal("96.0"), "t84_rate_r96p0_n6_b2"));
        cases.add(prodDates("T84-RATE-R96p0-N6-B3", "T84 independent re-probe (RATE): MNT 0.03 / 6 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 6, new BigDecimal("96.0"), "t84_rate_r96p0_n6_b3"));
        cases.add(prodDates("T84-RATE-R96p0-N6-B4", "T84 independent re-probe (RATE): MNT 0.04 / 6 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 6, new BigDecimal("96.0"), "t84_rate_r96p0_n6_b4"));
        cases.add(prodDates("T84-RATE-R96p0-N6-B5", "T84 independent re-probe (RATE): MNT 0.05 / 6 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 6, new BigDecimal("96.0"), "t84_rate_r96p0_n6_b5"));
        cases.add(prodDates("T84-RATE-R96p0-N12-B1", "T84 independent re-probe (RATE): MNT 0.01 / 12 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 12, new BigDecimal("96.0"), "t84_rate_r96p0_n12_b1"));
        cases.add(prodDates("T84-RATE-R96p0-N12-B2", "T84 independent re-probe (RATE): MNT 0.02 / 12 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 12, new BigDecimal("96.0"), "t84_rate_r96p0_n12_b2"));
        cases.add(prodDates("T84-RATE-R96p0-N12-B3", "T84 independent re-probe (RATE): MNT 0.03 / 12 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 12, new BigDecimal("96.0"), "t84_rate_r96p0_n12_b3"));
        cases.add(prodDates("T84-RATE-R96p0-N12-B4", "T84 independent re-probe (RATE): MNT 0.04 / 12 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 12, new BigDecimal("96.0"), "t84_rate_r96p0_n12_b4"));
        cases.add(prodDates("T84-RATE-R96p0-N12-B5", "T84 independent re-probe (RATE): MNT 0.05 / 12 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 12, new BigDecimal("96.0"), "t84_rate_r96p0_n12_b5"));
        cases.add(prodDates("T84-RATE-R96p0-N12-B6", "T84 independent re-probe (RATE): MNT 0.06 / 12 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(6).movePointLeft(2), 12, new BigDecimal("96.0"), "t84_rate_r96p0_n12_b6"));
        cases.add(prodDates("T84-RATE-R96p0-N56-B4", "T84 independent re-probe (RATE): MNT 0.04 / 56 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 56, new BigDecimal("96.0"), "t84_rate_r96p0_n56_b4"));
        cases.add(prodDates("T84-RATE-R96p0-N56-B5", "T84 independent re-probe (RATE): MNT 0.05 / 56 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 56, new BigDecimal("96.0"), "t84_rate_r96p0_n56_b5"));
        cases.add(prodDates("T84-RATE-R96p0-N56-B6", "T84 independent re-probe (RATE): MNT 0.06 / 56 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(6).movePointLeft(2), 56, new BigDecimal("96.0"), "t84_rate_r96p0_n56_b6"));
        cases.add(prodDates("T84-RATE-R96p0-N56-B7", "T84 independent re-probe (RATE): MNT 0.07 / 56 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(7).movePointLeft(2), 56, new BigDecimal("96.0"), "t84_rate_r96p0_n56_b7"));
        cases.add(prodDates("T84-RATE-R96p0-N56-B8", "T84 independent re-probe (RATE): MNT 0.08 / 56 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(8).movePointLeft(2), 56, new BigDecimal("96.0"), "t84_rate_r96p0_n56_b8"));
        cases.add(prodDates("T84-RATE-R96p0-N56-B9", "T84 independent re-probe (RATE): MNT 0.09 / 56 x 96.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(9).movePointLeft(2), 56, new BigDecimal("96.0"), "t84_rate_r96p0_n56_b9"));
        cases.add(prodDates("T84-TERM-R21p6-N1-B1", "T84 independent re-probe (TERM): MNT 0.01 / 1 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 1, new BigDecimal("21.6"), "t84_term_r21p6_n1_b1"));
        cases.add(prodDates("T84-TERM-R21p6-N1-B2", "T84 independent re-probe (TERM): MNT 0.02 / 1 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 1, new BigDecimal("21.6"), "t84_term_r21p6_n1_b2"));
        cases.add(prodDates("T84-TERM-R21p6-N1-B3", "T84 independent re-probe (TERM): MNT 0.03 / 1 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 1, new BigDecimal("21.6"), "t84_term_r21p6_n1_b3"));
        cases.add(prodDates("T84-TERM-R21p6-N5-B1", "T84 independent re-probe (TERM): MNT 0.01 / 5 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 5, new BigDecimal("21.6"), "t84_term_r21p6_n5_b1"));
        cases.add(prodDates("T84-TERM-R21p6-N5-B2", "T84 independent re-probe (TERM): MNT 0.02 / 5 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 5, new BigDecimal("21.6"), "t84_term_r21p6_n5_b2"));
        cases.add(prodDates("T84-TERM-R21p6-N5-B3", "T84 independent re-probe (TERM): MNT 0.03 / 5 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 5, new BigDecimal("21.6"), "t84_term_r21p6_n5_b3"));
        cases.add(prodDates("T84-TERM-R21p6-N5-B4", "T84 independent re-probe (TERM): MNT 0.04 / 5 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 5, new BigDecimal("21.6"), "t84_term_r21p6_n5_b4"));
        cases.add(prodDates("T84-TERM-R21p6-N5-B5", "T84 independent re-probe (TERM): MNT 0.05 / 5 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 5, new BigDecimal("21.6"), "t84_term_r21p6_n5_b5"));
        cases.add(prodDates("T84-TERM-R21p6-N7-B1", "T84 independent re-probe (TERM): MNT 0.01 / 7 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 7, new BigDecimal("21.6"), "t84_term_r21p6_n7_b1"));
        cases.add(prodDates("T84-TERM-R21p6-N7-B2", "T84 independent re-probe (TERM): MNT 0.02 / 7 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 7, new BigDecimal("21.6"), "t84_term_r21p6_n7_b2"));
        cases.add(prodDates("T84-TERM-R21p6-N7-B3", "T84 independent re-probe (TERM): MNT 0.03 / 7 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 7, new BigDecimal("21.6"), "t84_term_r21p6_n7_b3"));
        cases.add(prodDates("T84-TERM-R21p6-N7-B4", "T84 independent re-probe (TERM): MNT 0.04 / 7 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(4).movePointLeft(2), 7, new BigDecimal("21.6"), "t84_term_r21p6_n7_b4"));
        cases.add(prodDates("T84-TERM-R21p6-N7-B5", "T84 independent re-probe (TERM): MNT 0.05 / 7 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(5).movePointLeft(2), 7, new BigDecimal("21.6"), "t84_term_r21p6_n7_b5"));
        cases.add(prodDates("T84-TERM-R21p6-N7-B6", "T84 independent re-probe (TERM): MNT 0.06 / 7 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(6).movePointLeft(2), 7, new BigDecimal("21.6"), "t84_term_r21p6_n7_b6"));
        cases.add(prodDates("T84-TERM-R21p6-N30-B9", "T84 independent re-probe (TERM): MNT 0.09 / 30 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(9).movePointLeft(2), 30, new BigDecimal("21.6"), "t84_term_r21p6_n30_b9"));
        cases.add(prodDates("T84-TERM-R21p6-N30-B10", "T84 independent re-probe (TERM): MNT 0.10 / 30 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(10).movePointLeft(2), 30, new BigDecimal("21.6"), "t84_term_r21p6_n30_b10"));
        cases.add(prodDates("T84-TERM-R21p6-N30-B11", "T84 independent re-probe (TERM): MNT 0.11 / 30 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(11).movePointLeft(2), 30, new BigDecimal("21.6"), "t84_term_r21p6_n30_b11"));
        cases.add(prodDates("T84-TERM-R21p6-N30-B12", "T84 independent re-probe (TERM): MNT 0.12 / 30 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(12).movePointLeft(2), 30, new BigDecimal("21.6"), "t84_term_r21p6_n30_b12"));
        cases.add(prodDates("T84-TERM-R21p6-N30-B13", "T84 independent re-probe (TERM): MNT 0.13 / 30 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(13).movePointLeft(2), 30, new BigDecimal("21.6"), "t84_term_r21p6_n30_b13"));
        cases.add(prodDates("T84-TERM-R21p6-N30-B14", "T84 independent re-probe (TERM): MNT 0.14 / 30 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(14).movePointLeft(2), 30, new BigDecimal("21.6"), "t84_term_r21p6_n30_b14"));
        cases.add(prodDates("T84-TERM-R21p6-N60-B16", "T84 independent re-probe (TERM): MNT 0.16 / 60 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(16).movePointLeft(2), 60, new BigDecimal("21.6"), "t84_term_r21p6_n60_b16"));
        cases.add(prodDates("T84-TERM-R21p6-N60-B17", "T84 independent re-probe (TERM): MNT 0.17 / 60 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(17).movePointLeft(2), 60, new BigDecimal("21.6"), "t84_term_r21p6_n60_b17"));
        cases.add(prodDates("T84-TERM-R21p6-N60-B18", "T84 independent re-probe (TERM): MNT 0.18 / 60 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(18).movePointLeft(2), 60, new BigDecimal("21.6"), "t84_term_r21p6_n60_b18"));
        cases.add(prodDates("T84-TERM-R21p6-N60-B19", "T84 independent re-probe (TERM): MNT 0.19 / 60 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(19).movePointLeft(2), 60, new BigDecimal("21.6"), "t84_term_r21p6_n60_b19"));
        cases.add(prodDates("T84-TERM-R21p6-N60-B20", "T84 independent re-probe (TERM): MNT 0.20 / 60 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(20).movePointLeft(2), 60, new BigDecimal("21.6"), "t84_term_r21p6_n60_b20"));
        cases.add(prodDates("T84-TERM-R21p6-N60-B21", "T84 independent re-probe (TERM): MNT 0.21 / 60 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(21).movePointLeft(2), 60, new BigDecimal("21.6"), "t84_term_r21p6_n60_b21"));
        cases.add(prodDates("T84-TERM-R21p6-N120-B22", "T84 independent re-probe (TERM): MNT 0.22 / 120 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(22).movePointLeft(2), 120, new BigDecimal("21.6"), "t84_term_r21p6_n120_b22"));
        cases.add(prodDates("T84-TERM-R21p6-N120-B23", "T84 independent re-probe (TERM): MNT 0.23 / 120 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(23).movePointLeft(2), 120, new BigDecimal("21.6"), "t84_term_r21p6_n120_b23"));
        cases.add(prodDates("T84-TERM-R21p6-N120-B24", "T84 independent re-probe (TERM): MNT 0.24 / 120 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(24).movePointLeft(2), 120, new BigDecimal("21.6"), "t84_term_r21p6_n120_b24"));
        cases.add(prodDates("T84-TERM-R21p6-N120-B25", "T84 independent re-probe (TERM): MNT 0.25 / 120 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(25).movePointLeft(2), 120, new BigDecimal("21.6"), "t84_term_r21p6_n120_b25"));
        cases.add(prodDates("T84-TERM-R21p6-N120-B26", "T84 independent re-probe (TERM): MNT 0.26 / 120 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(26).movePointLeft(2), 120, new BigDecimal("21.6"), "t84_term_r21p6_n120_b26"));
        cases.add(prodDates("T84-TERM-R21p6-N120-B27", "T84 independent re-probe (TERM): MNT 0.27 / 120 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(27).movePointLeft(2), 120, new BigDecimal("21.6"), "t84_term_r21p6_n120_b27"));
        cases.add(prodDates("T84-TERM-R21p6-N240-B25", "T84 independent re-probe (TERM): MNT 0.25 / 240 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(25).movePointLeft(2), 240, new BigDecimal("21.6"), "t84_term_r21p6_n240_b25"));
        cases.add(prodDates("T84-TERM-R21p6-N240-B26", "T84 independent re-probe (TERM): MNT 0.26 / 240 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(26).movePointLeft(2), 240, new BigDecimal("21.6"), "t84_term_r21p6_n240_b26"));
        cases.add(prodDates("T84-TERM-R21p6-N240-B27", "T84 independent re-probe (TERM): MNT 0.27 / 240 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(27).movePointLeft(2), 240, new BigDecimal("21.6"), "t84_term_r21p6_n240_b27"));
        cases.add(prodDates("T84-TERM-R21p6-N240-B28", "T84 independent re-probe (TERM): MNT 0.28 / 240 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 240, new BigDecimal("21.6"), "t84_term_r21p6_n240_b28"));
        cases.add(prodDates("T84-TERM-R21p6-N240-B29", "T84 independent re-probe (TERM): MNT 0.29 / 240 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(29).movePointLeft(2), 240, new BigDecimal("21.6"), "t84_term_r21p6_n240_b29"));
        cases.add(prodDates("T84-TERM-R21p6-N240-B30", "T84 independent re-probe (TERM): MNT 0.30 / 240 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(30).movePointLeft(2), 240, new BigDecimal("21.6"), "t84_term_r21p6_n240_b30"));
        cases.add(prodDates("T84-TERM-R21p6-N360-B25", "T84 independent re-probe (TERM): MNT 0.25 / 360 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(25).movePointLeft(2), 360, new BigDecimal("21.6"), "t84_term_r21p6_n360_b25"));
        cases.add(prodDates("T84-TERM-R21p6-N360-B26", "T84 independent re-probe (TERM): MNT 0.26 / 360 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(26).movePointLeft(2), 360, new BigDecimal("21.6"), "t84_term_r21p6_n360_b26"));
        cases.add(prodDates("T84-TERM-R21p6-N360-B27", "T84 independent re-probe (TERM): MNT 0.27 / 360 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(27).movePointLeft(2), 360, new BigDecimal("21.6"), "t84_term_r21p6_n360_b27"));
        cases.add(prodDates("T84-TERM-R21p6-N360-B28", "T84 independent re-probe (TERM): MNT 0.28 / 360 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(28).movePointLeft(2), 360, new BigDecimal("21.6"), "t84_term_r21p6_n360_b28"));
        cases.add(prodDates("T84-TERM-R21p6-N360-B29", "T84 independent re-probe (TERM): MNT 0.29 / 360 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(29).movePointLeft(2), 360, new BigDecimal("21.6"), "t84_term_r21p6_n360_b29"));
        cases.add(prodDates("T84-TERM-R21p6-N360-B30", "T84 independent re-probe (TERM): MNT 0.30 / 360 x 21.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(30).movePointLeft(2), 360, new BigDecimal("21.6"), "t84_term_r21p6_n360_b30"));
        cases.add(prodDates("T84-LONG-R0p12-N120-B57", "T84 independent re-probe (LONG): MNT 0.57 / 120 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(57).movePointLeft(2), 120, new BigDecimal("0.12"), "t84_long_r0p12_n120_b57"));
        cases.add(prodDates("T84-LONG-R0p12-N120-B58", "T84 independent re-probe (LONG): MNT 0.58 / 120 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(58).movePointLeft(2), 120, new BigDecimal("0.12"), "t84_long_r0p12_n120_b58"));
        cases.add(prodDates("T84-LONG-R0p12-N120-B59", "T84 independent re-probe (LONG): MNT 0.59 / 120 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(59).movePointLeft(2), 120, new BigDecimal("0.12"), "t84_long_r0p12_n120_b59"));
        cases.add(prodDates("T84-LONG-R0p12-N120-B60", "T84 independent re-probe (LONG): MNT 0.60 / 120 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(60).movePointLeft(2), 120, new BigDecimal("0.12"), "t84_long_r0p12_n120_b60"));
        cases.add(prodDates("T84-LONG-R0p12-N120-B61", "T84 independent re-probe (LONG): MNT 0.61 / 120 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(61).movePointLeft(2), 120, new BigDecimal("0.12"), "t84_long_r0p12_n120_b61"));
        cases.add(prodDates("T84-LONG-R0p12-N120-B62", "T84 independent re-probe (LONG): MNT 0.62 / 120 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(62).movePointLeft(2), 120, new BigDecimal("0.12"), "t84_long_r0p12_n120_b62"));
        cases.add(prodDates("T84-LONG-R0p12-N240-B116", "T84 independent re-probe (LONG): MNT 1.16 / 240 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(116).movePointLeft(2), 240, new BigDecimal("0.12"), "t84_long_r0p12_n240_b116"));
        cases.add(prodDates("T84-LONG-R0p12-N240-B117", "T84 independent re-probe (LONG): MNT 1.17 / 240 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(117).movePointLeft(2), 240, new BigDecimal("0.12"), "t84_long_r0p12_n240_b117"));
        cases.add(prodDates("T84-LONG-R0p12-N240-B118", "T84 independent re-probe (LONG): MNT 1.18 / 240 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(118).movePointLeft(2), 240, new BigDecimal("0.12"), "t84_long_r0p12_n240_b118"));
        cases.add(prodDates("T84-LONG-R0p12-N240-B119", "T84 independent re-probe (LONG): MNT 1.19 / 240 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(119).movePointLeft(2), 240, new BigDecimal("0.12"), "t84_long_r0p12_n240_b119"));
        cases.add(prodDates("T84-LONG-R0p12-N240-B120", "T84 independent re-probe (LONG): MNT 1.20 / 240 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(120).movePointLeft(2), 240, new BigDecimal("0.12"), "t84_long_r0p12_n240_b120"));
        cases.add(prodDates("T84-LONG-R0p12-N240-B121", "T84 independent re-probe (LONG): MNT 1.21 / 240 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(121).movePointLeft(2), 240, new BigDecimal("0.12"), "t84_long_r0p12_n240_b121"));
        cases.add(prodDates("T84-LONG-R0p12-N360-B174", "T84 independent re-probe (LONG): MNT 1.74 / 360 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(174).movePointLeft(2), 360, new BigDecimal("0.12"), "t84_long_r0p12_n360_b174"));
        cases.add(prodDates("T84-LONG-R0p12-N360-B175", "T84 independent re-probe (LONG): MNT 1.75 / 360 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(175).movePointLeft(2), 360, new BigDecimal("0.12"), "t84_long_r0p12_n360_b175"));
        cases.add(prodDates("T84-LONG-R0p12-N360-B176", "T84 independent re-probe (LONG): MNT 1.76 / 360 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(176).movePointLeft(2), 360, new BigDecimal("0.12"), "t84_long_r0p12_n360_b176"));
        cases.add(prodDates("T84-LONG-R0p12-N360-B177", "T84 independent re-probe (LONG): MNT 1.77 / 360 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(177).movePointLeft(2), 360, new BigDecimal("0.12"), "t84_long_r0p12_n360_b177"));
        cases.add(prodDates("T84-LONG-R0p12-N360-B178", "T84 independent re-probe (LONG): MNT 1.78 / 360 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(178).movePointLeft(2), 360, new BigDecimal("0.12"), "t84_long_r0p12_n360_b178"));
        cases.add(prodDates("T84-LONG-R0p12-N360-B179", "T84 independent re-probe (LONG): MNT 1.79 / 360 x 0.12%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(179).movePointLeft(2), 360, new BigDecimal("0.12"), "t84_long_r0p12_n360_b179"));
        cases.add(prodDates("T84-LONG-R1p2-N120-B54", "T84 independent re-probe (LONG): MNT 0.54 / 120 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(54).movePointLeft(2), 120, new BigDecimal("1.2"), "t84_long_r1p2_n120_b54"));
        cases.add(prodDates("T84-LONG-R1p2-N120-B55", "T84 independent re-probe (LONG): MNT 0.55 / 120 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(55).movePointLeft(2), 120, new BigDecimal("1.2"), "t84_long_r1p2_n120_b55"));
        cases.add(prodDates("T84-LONG-R1p2-N120-B56", "T84 independent re-probe (LONG): MNT 0.56 / 120 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(56).movePointLeft(2), 120, new BigDecimal("1.2"), "t84_long_r1p2_n120_b56"));
        cases.add(prodDates("T84-LONG-R1p2-N120-B57", "T84 independent re-probe (LONG): MNT 0.57 / 120 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(57).movePointLeft(2), 120, new BigDecimal("1.2"), "t84_long_r1p2_n120_b57"));
        cases.add(prodDates("T84-LONG-R1p2-N120-B58", "T84 independent re-probe (LONG): MNT 0.58 / 120 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(58).movePointLeft(2), 120, new BigDecimal("1.2"), "t84_long_r1p2_n120_b58"));
        cases.add(prodDates("T84-LONG-R1p2-N120-B59", "T84 independent re-probe (LONG): MNT 0.59 / 120 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(59).movePointLeft(2), 120, new BigDecimal("1.2"), "t84_long_r1p2_n120_b59"));
        cases.add(prodDates("T84-LONG-R1p2-N240-B104", "T84 independent re-probe (LONG): MNT 1.04 / 240 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(104).movePointLeft(2), 240, new BigDecimal("1.2"), "t84_long_r1p2_n240_b104"));
        cases.add(prodDates("T84-LONG-R1p2-N240-B105", "T84 independent re-probe (LONG): MNT 1.05 / 240 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(105).movePointLeft(2), 240, new BigDecimal("1.2"), "t84_long_r1p2_n240_b105"));
        cases.add(prodDates("T84-LONG-R1p2-N240-B106", "T84 independent re-probe (LONG): MNT 1.06 / 240 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(106).movePointLeft(2), 240, new BigDecimal("1.2"), "t84_long_r1p2_n240_b106"));
        cases.add(prodDates("T84-LONG-R1p2-N240-B107", "T84 independent re-probe (LONG): MNT 1.07 / 240 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(107).movePointLeft(2), 240, new BigDecimal("1.2"), "t84_long_r1p2_n240_b107"));
        cases.add(prodDates("T84-LONG-R1p2-N240-B108", "T84 independent re-probe (LONG): MNT 1.08 / 240 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(108).movePointLeft(2), 240, new BigDecimal("1.2"), "t84_long_r1p2_n240_b108"));
        cases.add(prodDates("T84-LONG-R1p2-N240-B109", "T84 independent re-probe (LONG): MNT 1.09 / 240 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(109).movePointLeft(2), 240, new BigDecimal("1.2"), "t84_long_r1p2_n240_b109"));
        cases.add(prodDates("T84-LONG-R1p2-N360-B149", "T84 independent re-probe (LONG): MNT 1.49 / 360 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(149).movePointLeft(2), 360, new BigDecimal("1.2"), "t84_long_r1p2_n360_b149"));
        cases.add(prodDates("T84-LONG-R1p2-N360-B150", "T84 independent re-probe (LONG): MNT 1.50 / 360 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(150).movePointLeft(2), 360, new BigDecimal("1.2"), "t84_long_r1p2_n360_b150"));
        cases.add(prodDates("T84-LONG-R1p2-N360-B151", "T84 independent re-probe (LONG): MNT 1.51 / 360 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(151).movePointLeft(2), 360, new BigDecimal("1.2"), "t84_long_r1p2_n360_b151"));
        cases.add(prodDates("T84-LONG-R1p2-N360-B152", "T84 independent re-probe (LONG): MNT 1.52 / 360 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(152).movePointLeft(2), 360, new BigDecimal("1.2"), "t84_long_r1p2_n360_b152"));
        cases.add(prodDates("T84-LONG-R1p2-N360-B153", "T84 independent re-probe (LONG): MNT 1.53 / 360 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(153).movePointLeft(2), 360, new BigDecimal("1.2"), "t84_long_r1p2_n360_b153"));
        cases.add(prodDates("T84-LONG-R1p2-N360-B154", "T84 independent re-probe (LONG): MNT 1.54 / 360 x 1.2%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(154).movePointLeft(2), 360, new BigDecimal("1.2"), "t84_long_r1p2_n360_b154"));
        cases.add(prodDates("T84-LONG-R3p6-N120-B48", "T84 independent re-probe (LONG): MNT 0.48 / 120 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(48).movePointLeft(2), 120, new BigDecimal("3.6"), "t84_long_r3p6_n120_b48"));
        cases.add(prodDates("T84-LONG-R3p6-N120-B49", "T84 independent re-probe (LONG): MNT 0.49 / 120 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(49).movePointLeft(2), 120, new BigDecimal("3.6"), "t84_long_r3p6_n120_b49"));
        cases.add(prodDates("T84-LONG-R3p6-N120-B50", "T84 independent re-probe (LONG): MNT 0.50 / 120 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(50).movePointLeft(2), 120, new BigDecimal("3.6"), "t84_long_r3p6_n120_b50"));
        cases.add(prodDates("T84-LONG-R3p6-N120-B51", "T84 independent re-probe (LONG): MNT 0.51 / 120 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(51).movePointLeft(2), 120, new BigDecimal("3.6"), "t84_long_r3p6_n120_b51"));
        cases.add(prodDates("T84-LONG-R3p6-N120-B52", "T84 independent re-probe (LONG): MNT 0.52 / 120 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(52).movePointLeft(2), 120, new BigDecimal("3.6"), "t84_long_r3p6_n120_b52"));
        cases.add(prodDates("T84-LONG-R3p6-N120-B53", "T84 independent re-probe (LONG): MNT 0.53 / 120 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(53).movePointLeft(2), 120, new BigDecimal("3.6"), "t84_long_r3p6_n120_b53"));
        cases.add(prodDates("T84-LONG-R3p6-N240-B83", "T84 independent re-probe (LONG): MNT 0.83 / 240 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(83).movePointLeft(2), 240, new BigDecimal("3.6"), "t84_long_r3p6_n240_b83"));
        cases.add(prodDates("T84-LONG-R3p6-N240-B84", "T84 independent re-probe (LONG): MNT 0.84 / 240 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(84).movePointLeft(2), 240, new BigDecimal("3.6"), "t84_long_r3p6_n240_b84"));
        cases.add(prodDates("T84-LONG-R3p6-N240-B85", "T84 independent re-probe (LONG): MNT 0.85 / 240 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(85).movePointLeft(2), 240, new BigDecimal("3.6"), "t84_long_r3p6_n240_b85"));
        cases.add(prodDates("T84-LONG-R3p6-N240-B86", "T84 independent re-probe (LONG): MNT 0.86 / 240 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(86).movePointLeft(2), 240, new BigDecimal("3.6"), "t84_long_r3p6_n240_b86"));
        cases.add(prodDates("T84-LONG-R3p6-N240-B87", "T84 independent re-probe (LONG): MNT 0.87 / 240 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(87).movePointLeft(2), 240, new BigDecimal("3.6"), "t84_long_r3p6_n240_b87"));
        cases.add(prodDates("T84-LONG-R3p6-N240-B88", "T84 independent re-probe (LONG): MNT 0.88 / 240 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(88).movePointLeft(2), 240, new BigDecimal("3.6"), "t84_long_r3p6_n240_b88"));
        cases.add(prodDates("T84-LONG-R3p6-N360-B107", "T84 independent re-probe (LONG): MNT 1.07 / 360 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(107).movePointLeft(2), 360, new BigDecimal("3.6"), "t84_long_r3p6_n360_b107"));
        cases.add(prodDates("T84-LONG-R3p6-N360-B108", "T84 independent re-probe (LONG): MNT 1.08 / 360 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(108).movePointLeft(2), 360, new BigDecimal("3.6"), "t84_long_r3p6_n360_b108"));
        cases.add(prodDates("T84-LONG-R3p6-N360-B109", "T84 independent re-probe (LONG): MNT 1.09 / 360 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(109).movePointLeft(2), 360, new BigDecimal("3.6"), "t84_long_r3p6_n360_b109"));
        cases.add(prodDates("T84-LONG-R3p6-N360-B110", "T84 independent re-probe (LONG): MNT 1.10 / 360 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(110).movePointLeft(2), 360, new BigDecimal("3.6"), "t84_long_r3p6_n360_b110"));
        cases.add(prodDates("T84-LONG-R3p6-N360-B111", "T84 independent re-probe (LONG): MNT 1.11 / 360 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(111).movePointLeft(2), 360, new BigDecimal("3.6"), "t84_long_r3p6_n360_b111"));
        cases.add(prodDates("T84-LONG-R3p6-N360-B112", "T84 independent re-probe (LONG): MNT 1.12 / 360 x 3.6%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(112).movePointLeft(2), 360, new BigDecimal("3.6"), "t84_long_r3p6_n360_b112"));
        cases.add(prodDates("T84-TIE-R600p0-N60-B1", "T84 independent re-probe (TIE): MNT 0.01 / 60 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 60, new BigDecimal("600.0"), "t84_tie_r600p0_n60_b1"));
        cases.add(prodDates("T84-TIE-R600p0-N60-B2", "T84 independent re-probe (TIE): MNT 0.02 / 60 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 60, new BigDecimal("600.0"), "t84_tie_r600p0_n60_b2"));
        cases.add(prodDates("T84-TIE-R600p0-N90-B1", "T84 independent re-probe (TIE): MNT 0.01 / 90 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 90, new BigDecimal("600.0"), "t84_tie_r600p0_n90_b1"));
        cases.add(prodDates("T84-TIE-R600p0-N90-B2", "T84 independent re-probe (TIE): MNT 0.02 / 90 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 90, new BigDecimal("600.0"), "t84_tie_r600p0_n90_b2"));
        cases.add(prodDates("T84-TIE-R600p0-N108-B1", "T84 independent re-probe (TIE): MNT 0.01 / 108 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 108, new BigDecimal("600.0"), "t84_tie_r600p0_n108_b1"));
        cases.add(prodDates("T84-TIE-R600p0-N108-B2", "T84 independent re-probe (TIE): MNT 0.02 / 108 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 108, new BigDecimal("600.0"), "t84_tie_r600p0_n108_b2"));
        cases.add(prodDates("T84-TIE-R600p0-N120-B1", "T84 independent re-probe (TIE): MNT 0.01 / 120 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 120, new BigDecimal("600.0"), "t84_tie_r600p0_n120_b1"));
        cases.add(prodDates("T84-TIE-R600p0-N120-B2", "T84 independent re-probe (TIE): MNT 0.02 / 120 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 120, new BigDecimal("600.0"), "t84_tie_r600p0_n120_b2"));
        cases.add(prodDates("T84-TIE-R600p0-N150-B1", "T84 independent re-probe (TIE): MNT 0.01 / 150 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 150, new BigDecimal("600.0"), "t84_tie_r600p0_n150_b1"));
        cases.add(prodDates("T84-TIE-R600p0-N150-B2", "T84 independent re-probe (TIE): MNT 0.02 / 150 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 150, new BigDecimal("600.0"), "t84_tie_r600p0_n150_b2"));
        cases.add(prodDates("T84-TIE-R600p0-N200-B1", "T84 independent re-probe (TIE): MNT 0.01 / 200 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 200, new BigDecimal("600.0"), "t84_tie_r600p0_n200_b1"));
        cases.add(prodDates("T84-TIE-R600p0-N200-B2", "T84 independent re-probe (TIE): MNT 0.02 / 200 x 600.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 200, new BigDecimal("600.0"), "t84_tie_r600p0_n200_b2"));
        cases.add(prodDates("T84-TIE-R300p0-N100-B1", "T84 independent re-probe (TIE): MNT 0.01 / 100 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 100, new BigDecimal("300.0"), "t84_tie_r300p0_n100_b1"));
        cases.add(prodDates("T84-TIE-R300p0-N100-B2", "T84 independent re-probe (TIE): MNT 0.02 / 100 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 100, new BigDecimal("300.0"), "t84_tie_r300p0_n100_b2"));
        cases.add(prodDates("T84-TIE-R300p0-N100-B3", "T84 independent re-probe (TIE): MNT 0.03 / 100 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 100, new BigDecimal("300.0"), "t84_tie_r300p0_n100_b3"));
        cases.add(prodDates("T84-TIE-R300p0-N150-B1", "T84 independent re-probe (TIE): MNT 0.01 / 150 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 150, new BigDecimal("300.0"), "t84_tie_r300p0_n150_b1"));
        cases.add(prodDates("T84-TIE-R300p0-N150-B2", "T84 independent re-probe (TIE): MNT 0.02 / 150 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 150, new BigDecimal("300.0"), "t84_tie_r300p0_n150_b2"));
        cases.add(prodDates("T84-TIE-R300p0-N150-B3", "T84 independent re-probe (TIE): MNT 0.03 / 150 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 150, new BigDecimal("300.0"), "t84_tie_r300p0_n150_b3"));
        cases.add(prodDates("T84-TIE-R300p0-N175-B1", "T84 independent re-probe (TIE): MNT 0.01 / 175 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 175, new BigDecimal("300.0"), "t84_tie_r300p0_n175_b1"));
        cases.add(prodDates("T84-TIE-R300p0-N175-B2", "T84 independent re-probe (TIE): MNT 0.02 / 175 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 175, new BigDecimal("300.0"), "t84_tie_r300p0_n175_b2"));
        cases.add(prodDates("T84-TIE-R300p0-N175-B3", "T84 independent re-probe (TIE): MNT 0.03 / 175 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 175, new BigDecimal("300.0"), "t84_tie_r300p0_n175_b3"));
        cases.add(prodDates("T84-TIE-R300p0-N196-B1", "T84 independent re-probe (TIE): MNT 0.01 / 196 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 196, new BigDecimal("300.0"), "t84_tie_r300p0_n196_b1"));
        cases.add(prodDates("T84-TIE-R300p0-N196-B2", "T84 independent re-probe (TIE): MNT 0.02 / 196 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 196, new BigDecimal("300.0"), "t84_tie_r300p0_n196_b2"));
        cases.add(prodDates("T84-TIE-R300p0-N196-B3", "T84 independent re-probe (TIE): MNT 0.03 / 196 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 196, new BigDecimal("300.0"), "t84_tie_r300p0_n196_b3"));
        cases.add(prodDates("T84-TIE-R300p0-N220-B1", "T84 independent re-probe (TIE): MNT 0.01 / 220 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 220, new BigDecimal("300.0"), "t84_tie_r300p0_n220_b1"));
        cases.add(prodDates("T84-TIE-R300p0-N220-B2", "T84 independent re-probe (TIE): MNT 0.02 / 220 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 220, new BigDecimal("300.0"), "t84_tie_r300p0_n220_b2"));
        cases.add(prodDates("T84-TIE-R300p0-N220-B3", "T84 independent re-probe (TIE): MNT 0.03 / 220 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 220, new BigDecimal("300.0"), "t84_tie_r300p0_n220_b3"));
        cases.add(prodDates("T84-TIE-R300p0-N260-B1", "T84 independent re-probe (TIE): MNT 0.01 / 260 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(1).movePointLeft(2), 260, new BigDecimal("300.0"), "t84_tie_r300p0_n260_b1"));
        cases.add(prodDates("T84-TIE-R300p0-N260-B2", "T84 independent re-probe (TIE): MNT 0.02 / 260 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(2).movePointLeft(2), 260, new BigDecimal("300.0"), "t84_tie_r300p0_n260_b2"));
        cases.add(prodDates("T84-TIE-R300p0-N260-B3", "T84 independent re-probe (TIE): MNT 0.03 / 260 x 300.0%", LocalDate.of(2024, 1, 1), LocalDate.of(2024, 1, 1), new BigDecimal(3).movePointLeft(2), 260, new BigDecimal("300.0"), "t84_tie_r300p0_n260_b3"));

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"pass\": \"t83\",\n");
        sb.append("  \"harness\": \"CaptureT84.java\",\n");
        sb.append("  \"extends\": \"Capture3g.java / capture-prod3g-raw.json — same rig, same attestation, same emitted columns, same emission rules, with pass 3i's CurrencyData.inMultiplesOf / installmentAmountInMultiplesOf field split carried over (both null on every case here, so both keys emit exactly as pass 3g emitted them). NEW CASE LIST: two rig calibrations byte-identical to pass 3g T64-ZP-A and T64-ZP-B, then a CONTIGUOUS PRINCIPAL SWEEP in minor units over four annual rates x eight repayment counts, taken for gate G-8 (task T83) to measure the exact boundary of the region where the reference oracle emits a graded-domain schedule whose outstanding-balance column does not reach zero. Every sweep cell is emitted, clean or not; this harness classifies nothing.\",\n");
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
        try (InputStream in = CaptureT84.class.getResourceAsStream("/git.properties")) {
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
                ? "/cap/src/CaptureT84.java:/cap/src/EmbeddableProgressiveLoanScheduleGenerator.java"
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
                ? "/cap/out/capture-prod3g-classpath-sha256.txt" : System.getenv("ATTEST_CLASSPATH_OUT");
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
                c.currencyMultiplesOf(), c.currencyCode(), c.currencyCode());

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
        b.append("        \"currencyInMultiplesOf\": ").append(c.currencyMultiplesOf()).append(",\n");
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
